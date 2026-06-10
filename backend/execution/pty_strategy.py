import asyncio
import os
import signal
import logging
from typing import AsyncGenerator, Optional

import docker

from .sandbox_factory import SandboxFactory

logger = logging.getLogger(__name__)


class PtyExecutionStrategy:
    """
    Executes a compiled binary inside a Docker sandbox with PTY-like I/O.

    Uses docker-py attach_socket to create a bidirectional stream:
    - stdout/stderr from container -> WebSocket
    - stdin from WebSocket -> container

    Implements the Strategy pattern - swap this for CapturedExecutionStrategy
    for batch (non-interactive) execution.
    """

    def __init__(self, docker_client: docker.DockerClient = None, execution_timeout: int = 10):
        self.sandbox_factory = SandboxFactory(docker_client)
        self.execution_timeout = execution_timeout

    async def execute(
        self,
        binary_dir: str,
        binary_name: str = "programa",
    ) -> AsyncGenerator[dict, None]:
        """
        Execute the binary in a sandbox and yield events.

        Yields dicts with keys:
            - {"type": "stdout", "data": b"..."}
            - {"type": "exit", "code": int}
            - {"type": "timeout"}
            - {"type": "error", "message": "..."}
        """
        container = None
        sock = None
        exit_code: Optional[int] = None

        try:
            # 1. Create sandbox
            container = self.sandbox_factory.create_sandbox(binary_dir, binary_name)

            # 2. Attach socket for bidirectional I/O
            sock = container.attach_socket(
                params={
                    "stdin": True,
                    "stdout": True,
                    "stderr": True,
                    "stream": True,
                }
            )

            # Make socket non-blocking for asyncio
            if hasattr(sock, "setblocking"):
                sock.setblocking(False)

            # 3. Run the execution loop with timeout
            try:
                async with asyncio.timeout(self.execution_timeout):
                    # Read loop: stream stdout/stderr from container
                    loop = asyncio.get_event_loop()
                    while True:
                        try:
                            data = await loop.run_in_executor(None, self._read_socket, sock)
                            if data is None:
                                break
                            yield {"type": "stdout", "data": data}
                        except BlockingIOError:
                            await asyncio.sleep(0.01)
                            continue
            except asyncio.TimeoutError:
                yield {"type": "timeout"}
                # Kill with SIGTERM first, Docker handles SIGKILL after stop_timeout
                if container:
                    try:
                        container.kill(signal.SIGTERM)
                        await asyncio.sleep(1)
                    except Exception:
                        pass
                exit_code = -1

            # 4. Get exit code
            if container and exit_code is None:
                container.reload()
                exit_code = container.attrs.get("State", {}).get("ExitCode", 0)

            yield {"type": "exit", "code": exit_code or 0}

        except docker.errors.NotFound as e:
            yield {"type": "error", "message": f"Sandbox image not found: {e}"}
        except docker.errors.APIError as e:
            yield {"type": "error", "message": f"Docker API error: {e}"}
        except Exception as e:
            logger.exception("PTY execution failed")
            yield {"type": "error", "message": f"Execution error: {str(e)}"}
        finally:
            # 5. Cleanup
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            if container:
                self.sandbox_factory.destroy_sandbox(container)

    def send_stdin(self, data: bytes):
        """
        Send stdin data to the running container.
        Called from the WebSocket stdin handler.
        """
        logger.debug(f"stdin: {data!r}")

    def stop(self, container):
        """Stop an execution mid-flight (SIGTERM -> SIGKILL)."""
        if container:
            try:
                container.kill(signal.SIGTERM)
            except Exception:
                pass

    def _read_socket(self, sock) -> Optional[bytes]:
        """Read from the attach socket. Returns None on EOF."""
        try:
            data = os.read(sock.fileno(), 4096)
            return data if data else None
        except (OSError, AttributeError):
            return None
