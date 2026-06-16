"""Tests for sandbox factory (sandbox.py)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.sandbox import SandboxFactory, SandboxConfig
from app.config import config


class TestSandboxConfig:
    """Tests for SandboxConfig dataclass."""

    def test_default_config(self):
        """Default config should have correct security values."""
        cfg = SandboxConfig(image="simples-runner:latest")
        assert cfg.network_mode == "none"
        assert cfg.mem_limit == "128m"
        assert cfg.memswap_limit == "128m"
        assert cfg.cpu_quota == 50000
        assert cfg.pids_limit == 64
        assert cfg.read_only is True
        assert cfg.tmpfs == {"/tmp": "size=8m"}
        assert cfg.user == "65534:65534"
        assert cfg.cap_drop == ["ALL"]
        assert cfg.stop_timeout == 12

    def test_custom_image(self):
        """Config should accept custom image name."""
        cfg = SandboxConfig(image="my-runner:v2")
        assert cfg.image == "my-runner:v2"


class TestSandboxFactory:
    """Tests for SandboxFactory."""

    def test_init_default_image(self):
        """Factory should use default image from config."""
        factory = SandboxFactory()
        assert factory.image == config.sandbox_image
        assert factory._client is None  # Lazy init

    def test_init_custom_image(self):
        """Factory should accept custom image."""
        factory = SandboxFactory(image="custom-runner:latest")
        assert factory.image == "custom-runner:latest"
        assert factory._client is None  # Lazy init

    def test_create_default_config(self):
        """Default config from factory should match SandboxConfig defaults."""
        factory = SandboxFactory()
        cfg = factory.create_default_config()
        assert cfg.image == config.sandbox_image
        assert cfg.network_mode == "none"

    def test_cleanup_container(self):
        """cleanup_container should force-remove the container."""
        factory = SandboxFactory()
        mock_container = MagicMock()

        factory.cleanup_container(mock_container)
        mock_container.remove.assert_called_once_with(force=True)

    def test_cleanup_container_error(self):
        """cleanup_container should not raise on error."""
        factory = SandboxFactory()
        mock_container = MagicMock()
        mock_container.remove.side_effect = Exception("Remove failed")

        # Should not raise
        factory.cleanup_container(mock_container)
