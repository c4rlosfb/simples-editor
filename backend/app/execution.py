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

        try:
            container = self.client.containers.run(
                image=self.image,
                command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
                volumes={str(binary_dir): {"bind": "/sandbox", "mode": "ro"}},
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

            sock = container.attach_socket(
                params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1}
            )
            sock._sock.setblocking(False)

            loop = asyncio.get_event_loop()

            async def pty_to_ws() -> None:
                while True:
                    try:
                        data = await loop.run_in_executor(
                            None, sock._sock.recv, 4096
                        )
                        if not data:
                            break
                        await ws.send(
                            json.dumps({
                                "type": "stdout",
                                "data": data.decode("utf-8", errors="replace"),
                            })
                        )
                    except BlockingIOError:
                        await asyncio.sleep(0.01)

            async def stdin_to_pty() -> None:
                """Read stdin from the asyncio.Queue and forward to PTY.

                Replaces the old ws_to_pty() that consumed from the WebSocket
                directly. Now reads from stdin_queue (populated by the main
                ws_run loop) and checks stop_event for termination signals.
                """
                if stdin_queue is None:
                    # No stdin support — just wait for stop signal or pty EOF
                    while True:
                        if stop_event and stop_event.is_set():
                            container.kill(signal="SIGTERM")
                            break
                        await asyncio.sleep(0.1)
                    return

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
                        container.kill(signal="SIGTERM")
                        break

                    if get_task in done:
                        data = get_task.result()
                        sock._sock.sendall(data.encode("utf-8"))
                        get_task = asyncio.create_task(stdin_queue.get())

            timed_out = False
            try:
                await asyncio.wait_for(
                    asyncio.gather(pty_to_ws(), stdin_to_pty()),
                    timeout=timeout_s,
                )
            except asyncio.TimeoutError:
                container.kill(signal="SIGTERM")
                await asyncio.sleep(1)
                try:
                    container.kill(signal="SIGKILL")
                except docker.errors.APIError:
                    pass
                timed_out = True

            result = container.wait(timeout=5)
            exit_code = result["StatusCode"]

        except docker.errors.ImageNotFound:
            logger.error("sandbox_image_not_found: image=%s", self.image)
            await ws.send(json.dumps({
                "type": "internal_error",
                "message": f"Sandbox image '{self.image}' not found",
            }))
            exit_code = -1
            timed_out = False
        except docker.errors.APIError as e:
            logger.error("docker_api_error: error=%s", str(e))
            await ws.send(json.dumps({
                "type": "internal_error",
                "message": f"Docker error: {e.explanation if hasattr(e, 'explanation') else str(e)}",
            }))
            exit_code = -1
            timed_out = False
        except Exception as e:
            logger.exception("execution_unexpected_error")
            try:
                await ws.send(json.dumps({
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
        await ws.send(json.dumps({
            "type": "internal_error",
            "message": "Captured execution not yet implemented",
        }))
        return ExecutionResult(exit_code=-1, duration_ms=0, timed_out=False)
