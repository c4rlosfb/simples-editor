import docker
import logging

logger = logging.getLogger(__name__)

SANDBOX_IMAGE = "simples-runner:latest"
DEFAULT_MEM_LIMIT = "128m"
DEFAULT_CPU_QUOTA = 50000       # 50% of 1 CPU
DEFAULT_PIDS_LIMIT = 64
DEFAULT_STOP_TIMEOUT = 12       # seconds before SIGKILL


class SandboxFactory:
    """Centralizes creation of sandbox containers with consistent security limits."""

    def __init__(self, docker_client: docker.DockerClient = None):
        self.client = docker_client or docker.from_env()

    def create_sandbox(
        self,
        binary_dir: str,
        binary_name: str = "programa",
        mem_limit: str = DEFAULT_MEM_LIMIT,
        cpu_quota: int = DEFAULT_CPU_QUOTA,
        pids_limit: int = DEFAULT_PIDS_LIMIT,
        stop_timeout: int = DEFAULT_STOP_TIMEOUT,
    ):
        """
        Create and start a sandbox container for executing a compiled binary.
        Returns the container object (already started).
        """
        binary_path = f"/sandbox/{binary_name}"

        container = self.client.containers.run(
            image=SANDBOX_IMAGE,
            command=["/usr/bin/qemu-i386-static", binary_path],
            volumes={
                binary_dir: {"bind": "/sandbox", "mode": "ro"},
            },
            network_mode="none",
            mem_limit=mem_limit,
            cpu_quota=cpu_quota,
            pids_limit=pids_limit,
            read_only=True,
            tmpfs={"/tmp": "size=8m"},
            user="65534:65534",       # nobody user
            detach=True,
            stdin_open=True,
            tty=True,
            remove=False,             # we destroy manually after bridge closes
            stop_timeout=stop_timeout,
        )

        logger.info(f"Sandbox container {container.id[:12]} started")
        return container

    def destroy_sandbox(self, container):
        """Forcefully remove a sandbox container."""
        try:
            container.remove(force=True)
            logger.info(f"Sandbox container {container.id[:12]} destroyed")
        except Exception as e:
            logger.warning(f"Failed to destroy sandbox {container.id[:12]}: {e}")
