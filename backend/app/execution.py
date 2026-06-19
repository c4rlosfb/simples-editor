"""Execution strategies — Strategy pattern for running compiled binaries.

Implements the Strategy pattern described in PRD §7.4.
Currently provides PtyExecutionStrategy for interactive TTY execution.
Reference implementation adapted from PRD Appendix B.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import docker
from docker.models.containers import Container

from app.config import config

logger = logging.getLogger("simples.executor")


def _discover_volume_name(mount_point: str) -> str:
    """Discover the Docker volume name mounted at mount_point.

    On Docker Compose, named volumes are prefixed with the project name
    (e.g. simples-editor_simples_tmp). We need the actual volume name
    to mount it into sandbox containers.
    """
    import os
    # Parse /proc/mounts or /proc/self/mountinfo to find the volume
    try:
        with open("/proc/self/mountinfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 10 and parts[4] == mount_point:
                    # Format: id parent major:minor root mount_point ... - type device
                    # root (index 3) contains the volume path on Docker
                    root = parts[3] if len(parts) > 3 else ""
                    if "volumes/" in root:
                        vol_name = root.split("volumes/")[1].split("/")[0]
                        return vol_name
    except Exception:
        pass

    # Fallback: check /proc/mounts
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == mount_point:
                    device = parts[0]
                    if "volumes/" in device:
                        vol_name = device.split("volumes/")[1].split("/")[0]
                        return vol_name
    except Exception:
        pass

    # Last fallback: try common docker-compose project names
    for project in ["simples-editor", "simples-online"]:
        vol = f"{project}_simples_tmp"
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "volume", "inspect", vol],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                return vol
        except Exception:
            pass

    # Desperate fallback
    return "simples_tmp"


@dataclass
class ExecutionResult:
    """Result of a binary execution."""

    exit_code: int
    duration_ms: int
    timed_out: bool


class ExecutionStrategy(ABC):
    """Abstract strategy for executing compiled binaries."""

    @abstractmethod
    async def execute(
        self, binary_dir: Path, ws: Any, timeout_s: int,
        stdin_queue: Optional[asyncio.Queue] = None,
        stop_event: Optional[asyncio.Event] = None,
    ) -> ExecutionResult:
        ...


class PtyExecutionStrategy(ExecutionStrategy):
    """Interactive execution via Docker container with TTY.

    Spawns a sandboxed Docker container and bridges its stdio
    to a WebSocket connection for interactive `leia`/`escreva` support.

    stdin/stop messages are received via stdin_queue and stop_event
    (asyncio.Queue and asyncio.Event) instead of consuming from the
    WebSocket directly — the WebSocket is consumed exclusively by
    the main ws_run loop to prevent dual-consumer races.
    """

    def __init__(self, image: Optional[str] = None):
        self.image = image or config.sandbox_image
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy Docker client initialization."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    async def execute(
        self, binary_dir: Path, ws: Any, timeout_s: int,
        stdin_queue: Optional[asyncio.Queue] = None,
        stop_event: Optional[asyncio.Event] = None,
    ) -> ExecutionResult:
        """Execute the binary and bridge I/O to WebSocket."""
        container: Optional[Container] = None
        sock: Any = None
        start = time.monotonic()

        # Calculate the binary path inside the sandbox.
        # binary_dir is like /tmp/simples/sim-abc123/
        # Discover the actual Docker volume name mounted at /tmp/simples
        # (docker-compose prefixes it with the project name)
        tmp_base = config.tmp_base  # e.g. /tmp/simples
        rel_path = binary_dir.relative_to(tmp_base)
        sandbox_binary = f"/mnt/simples/{rel_path}/programa"

        # Discover the volume name from the backend container's mounts
        volume_name = _discover_volume_name(str(tmp_base))

        try:
            container = self.client.containers.run(
                image=self.image,
                command=["/usr/bin/qemu-i386-static", sandbox_binary],
                volumes={volume_name: {"bind": "/mnt/simples", "mode": "ro"}},
                network_mode="none",
                mem_limit="128m",
                memswap_limit="128m",
                cpu_quota=50000,
                pids_limit=64,
                read_only=True,
                tmpfs={"/tmp": "size=8m"},
                user="65534:65534",
                cap_drop=["ALL"],
                stdin_open=True,
                tty=True,
                detach=True,
                stop_timeout=12,  # Hard timeout before SIGKILL (PRD §11.3)
            )

            loop = asyncio.get_event_loop()

            async def pty_to_ws() -> None:
                """Stream container output via logs(follow=True) in a thread."""
                import queue
                import threading

                log_queue: queue.Queue = queue.Queue()

                def _stream_logs():
                    try:
                        for chunk in container.logs(
                            stdout=True, stderr=True, stream=True, follow=True
                        ):
                            if chunk:
                                log_queue.put(chunk)
                    except Exception:
                        pass
                    finally:
                        log_queue.put(None)  # Sentinel

                thread = threading.Thread(target=_stream_logs, daemon=True)
                thread.start()

                while True:
                    chunk = await loop.run_in_executor(None, log_queue.get)
                    if chunk is None:
                        break
                    ws.send(
                        json.dumps({
                            "type": "stdout",
                            "data": chunk.decode("utf-8", errors="replace"),
                        })
                    )

            async def stdin_to_pty() -> None:
                """Read stdin from the asyncio.Queue and forward to container."""
                if stdin_queue is None:
                    # No stdin support — just wait for stop signal or container exit
                    while True:
                        if stop_event and stop_event.is_set():
                            try:
                                container.kill(signal="SIGTERM")
                            except Exception:
                                pass
                            break
                        # Check if container exited
                        try:
                            container.reload()
                            if container.status != "running":
                                break
                        except Exception:
                            pass
                        await asyncio.sleep(0.1)
                    return

                # Attach socket for stdin only
                stdin_sock = container.attach_socket(
                    params={"stdin": 1, "stream": 1}
                )

                get_task = asyncio.create_task(stdin_queue.get())
                stop_task = asyncio.create_task(stop_event.wait()) if stop_event else None

                while True:
                    tasks = [get_task]
                    if stop_task:
                        tasks.append(stop_task)

                    done, _ = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )

                    if stop_task and stop_task in done:
                        try:
                            container.kill(signal="SIGTERM")
                        except Exception:
                            pass
                        break

                    if get_task in done:
                        data = get_task.result()
                        try:
                            stdin_sock._sock.sendall(data.encode("utf-8"))
                        except Exception:
                            pass
                        get_task = asyncio.create_task(stdin_queue.get())

            timed_out = False
            try:
                await asyncio.wait_for(
                    asyncio.gather(pty_to_ws(), stdin_to_pty()),
                    timeout=timeout_s,
                )
            except asyncio.TimeoutError:
                try:
                    container.kill(signal="SIGTERM")
                except Exception:
                    pass
                await asyncio.sleep(1)
                try:
                    container.kill(signal="SIGKILL")
                except Exception:
                    pass
                timed_out = True

            result = container.wait(timeout=5)
            exit_code = result["StatusCode"]

        except docker.errors.ImageNotFound:
            logger.error("sandbox_image_not_found: image=%s", self.image)
            ws.send(json.dumps({
                "type": "internal_error",
                "message": f"Sandbox image '{self.image}' not found",
            }))
            exit_code = -1
            timed_out = False
        except docker.errors.APIError as e:
            logger.error("docker_api_error: error=%s", str(e))
            ws.send(json.dumps({
                "type": "internal_error",
                "message": f"Docker error: {e.explanation if hasattr(e, 'explanation') else str(e)}",
            }))
            exit_code = -1
            timed_out = False
        except Exception as e:
            logger.exception("execution_unexpected_error")
            try:
                ws.send(json.dumps({
                    "type": "internal_error",
                    "message": f"Execution error: {e}",
                }))
            except Exception:
                pass
            exit_code = -1
            timed_out = False
        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    logger.warning("container_remove_failed")

        duration_ms = int((time.monotonic() - start) * 1000)
        return ExecutionResult(
            exit_code=exit_code,
            duration_ms=duration_ms,
            timed_out=timed_out,
        )


class CapturedExecutionStrategy(ExecutionStrategy):
    """Non-interactive execution via subprocess (no TTY/leia support)."""

    async def execute(
        self, binary_dir: Path, ws: Any, timeout_s: int,
        stdin_queue: Optional[asyncio.Queue] = None,
        stop_event: Optional[asyncio.Event] = None,
    ) -> ExecutionResult:
        ws.send(json.dumps({
            "type": "internal_error",
            "message": "Captured execution not yet implemented",
        }))
        return ExecutionResult(exit_code=-1, duration_ms=0, timed_out=False)
