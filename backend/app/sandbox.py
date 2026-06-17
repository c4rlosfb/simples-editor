"""Sandbox factory — centralized Docker container creation.

Implements the Factory pattern described in PRD §7.4.
Ensures all sandbox containers are created with consistent
security limits defined in PRD §11.2.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import docker

from app.config import config

logger = logging.getLogger("simples.sandbox")


@dataclass
class SandboxConfig:
    """Security and resource constraints for a sandbox container."""

    image: str
    network_mode: str = "none"
    mem_limit: str = "128m"
    memswap_limit: str = "128m"
    cpu_quota: int = 50000
    pids_limit: int = 64
    read_only: bool = True
    tmpfs: Optional[dict[str, str]] = None
    user: str = "65534:65534"
    cap_drop: Optional[list[str]] = None
    stdin_open: bool = True
    tty: bool = True
    detach: bool = True
    stop_timeout: int = 12

    def __post_init__(self):
        if self.tmpfs is None:
            self.tmpfs = {"/tmp": "size=8m"}
        if self.cap_drop is None:
            self.cap_drop = ["ALL"]


class SandboxFactory:
    """Factory for creating sandbox containers with consistent security profiles."""

    def __init__(self, image: Optional[str] = None):
        self.image = image or config.sandbox_image
        self._client: Any = None

    @property
    def client(self) -> Any:
        """Lazy Docker client initialization."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def create_default_config(self) -> SandboxConfig:
        """Return a SandboxConfig with all security defaults."""
        return SandboxConfig(image=self.image)

    def create_container(self, binary_dir: Path) -> Any:
        """Create and start a sandbox container."""
        cfg = self.create_default_config()

        container = self.client.containers.run(
            image=cfg.image,
            command=["/usr/bin/qemu-i386-static", "/sandbox/programa"],
            volumes={str(binary_dir): {"bind": "/sandbox", "mode": "ro"}},
            network_mode=cfg.network_mode,
            mem_limit=cfg.mem_limit,
            memswap_limit=cfg.memswap_limit,
            cpu_quota=cfg.cpu_quota,
            pids_limit=cfg.pids_limit,
            read_only=cfg.read_only,
            tmpfs=cfg.tmpfs,
            user=cfg.user,
            cap_drop=cfg.cap_drop,
            stdin_open=cfg.stdin_open,
            tty=cfg.tty,
            detach=cfg.detach,
            stop_timeout=cfg.stop_timeout,
        )

        logger.info("sandbox_created: container_id=%s", container.short_id)
        return container

    def cleanup_container(self, container: Any) -> None:
        """Force-remove a sandbox container."""
        try:
            container.remove(force=True)
            logger.info("sandbox_removed: container_id=%s", container.short_id)
        except Exception:
            logger.warning("sandbox_remove_failed: container_id=%s", container.short_id)
