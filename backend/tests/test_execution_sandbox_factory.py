"""Tests for app/sandbox.py — SandboxFactory (production module)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.sandbox import SandboxConfig, SandboxFactory


class TestSandboxFactory:
    """Tests for SandboxFactory in app.sandbox (production)."""

    # ── constructor / image ──────────────────────────────────────────

    def test_init_default_image(self):
        """SandboxFactory() should use the default sandbox image from config."""
        from app.config import config

        factory = SandboxFactory()
        assert factory.image == config.sandbox_image
        assert factory._client is None  # lazy init

    def test_init_custom_image(self):
        """SandboxFactory(image=...) should accept a custom image name."""
        factory = SandboxFactory(image="my-runner:latest")
        assert factory.image == "my-runner:latest"
        assert factory._client is None  # lazy init

    # ── client property (lazy docker.from_env) ───────────────────────

    @patch("app.sandbox.docker.from_env")
    def test_client_lazy_init(self, mock_from_env):
        """client property should lazily call docker.from_env() on first access."""
        mock_docker_client = MagicMock()
        mock_from_env.return_value = mock_docker_client

        factory = SandboxFactory()
        assert factory._client is None

        # first access — should call from_env
        client = factory.client
        assert client is mock_docker_client
        mock_from_env.assert_called_once()

        # second access — should return cached client
        client2 = factory.client
        assert client2 is mock_docker_client
        mock_from_env.assert_called_once()  # still only one call

    # ── create_default_config ────────────────────────────────────────

    def test_create_default_config_returns_sandbox_config(self):
        """create_default_config() should return a SandboxConfig instance."""
        factory = SandboxFactory(image="test-image:v1")
        cfg = factory.create_default_config()

        assert isinstance(cfg, SandboxConfig)
        assert cfg.image == "test-image:v1"

    def test_create_default_config_security_defaults(self):
        """Default config should have the security limits from PRD §11.2."""
        factory = SandboxFactory(image="test-image:v1")
        cfg = factory.create_default_config()

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
        assert cfg.stdin_open is True
        assert cfg.tty is True
        assert cfg.detach is True

    # ── create_container ─────────────────────────────────────────────

    @patch("app.sandbox.docker.from_env")
    def test_create_container_calls_docker_with_security_params(
        self, mock_from_env
    ):
        """create_container should run a container with all security constraints."""
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_container.short_id = "abc123def"
        mock_client.containers.run.return_value = mock_container

        import tempfile

        factory = SandboxFactory(image="test-image:v1")
        with tempfile.TemporaryDirectory() as tmpdir:
            binary_dir = Path(tmpdir)

            result = factory.create_container(binary_dir)

            assert result is mock_container
            mock_client.containers.run.assert_called_once()

            call_kwargs = mock_client.containers.run.call_args[1]
            assert call_kwargs["image"] == "test-image:v1"
            assert call_kwargs["command"] == [
                "/usr/bin/qemu-i386-static",
                "/sandbox/programa",
            ]
            assert call_kwargs["network_mode"] == "none"
            assert call_kwargs["mem_limit"] == "128m"
            assert call_kwargs["memswap_limit"] == "128m"
            assert call_kwargs["cpu_quota"] == 50000
            assert call_kwargs["pids_limit"] == 64
            assert call_kwargs["read_only"] is True
            assert call_kwargs["user"] == "65534:65534"
            assert call_kwargs["cap_drop"] == ["ALL"]
            assert call_kwargs["stop_timeout"] == 12
            assert call_kwargs["detach"] is True
            assert call_kwargs["tty"] is True
            assert call_kwargs["stdin_open"] is True

            # volumes: binary_dir → /sandbox (read-only)
            assert str(binary_dir) in call_kwargs["volumes"]
            vol_cfg = call_kwargs["volumes"][str(binary_dir)]
            assert vol_cfg["bind"] == "/sandbox"
            assert vol_cfg["mode"] == "ro"

            # tmpfs for /tmp
            assert call_kwargs["tmpfs"] == {"/tmp": "size=8m"}

    @patch("app.sandbox.docker.from_env")
    def test_create_container_uses_factory_image(self, mock_from_env):
        """create_container should use the image set at factory init time."""
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.return_value = MagicMock()

        factory = SandboxFactory(image="custom-sandbox:v3")
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            factory.create_container(Path(tmpdir))

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["image"] == "custom-sandbox:v3"

    # ── cleanup_container ────────────────────────────────────────────

    def test_cleanup_container_force_removes(self):
        """cleanup_container should call container.remove(force=True)."""
        factory = SandboxFactory()
        mock_container = MagicMock()
        mock_container.short_id = "abc123def"

        factory.cleanup_container(mock_container)
        mock_container.remove.assert_called_once_with(force=True)

    def test_cleanup_container_suppresses_errors(self):
        """cleanup_container should not raise when remove fails."""
        factory = SandboxFactory()
        mock_container = MagicMock()
        mock_container.short_id = "abc123def"
        mock_container.remove.side_effect = Exception("Remove failed")

        # should not raise
        factory.cleanup_container(mock_container)
        mock_container.remove.assert_called_once_with(force=True)
