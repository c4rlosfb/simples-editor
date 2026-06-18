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

    @patch("app.sandbox.docker.from_env")
    def test_client_lazy_init(self, mock_from_env):
        """Client should be lazily initialized on first access."""
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        factory = SandboxFactory()
        assert factory._client is None

        client = factory.client
        assert client == mock_client
        mock_from_env.assert_called_once()

        # Second access should return cached client
        client2 = factory.client
        assert client2 == mock_client
        mock_from_env.assert_called_once()  # Still only called once

    @patch("app.sandbox.docker.from_env")
    def test_create_container(self, mock_from_env):
        """create_container should call docker with all security parameters."""
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        factory = SandboxFactory(image="test-image:v1")
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            binary_dir = Path(tmpdir)

            container = factory.create_container(binary_dir)

            assert container == mock_container
            mock_client.containers.run.assert_called_once()
            call_kwargs = mock_client.containers.run.call_args[1]

            assert call_kwargs["image"] == "test-image:v1"
            assert call_kwargs["network_mode"] == "none"
            assert call_kwargs["mem_limit"] == "128m"
            assert call_kwargs["memswap_limit"] == "128m"
            assert call_kwargs["cpu_quota"] == 50000
            assert call_kwargs["pids_limit"] == 64
            assert call_kwargs["read_only"] is True
            assert call_kwargs["user"] == "65534:65534"
            assert call_kwargs["cap_drop"] == ["ALL"]
            assert call_kwargs["stop_timeout"] == 12

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
