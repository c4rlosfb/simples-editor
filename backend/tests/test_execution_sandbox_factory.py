"""Tests for execution/sandbox_factory.py."""

from unittest.mock import MagicMock, patch

import pytest


class TestSandboxFactory:
    """Tests for SandboxFactory in execution package."""

    def test_init_with_client(self):
        """Should accept a docker client."""
        from backend.execution.sandbox_factory import SandboxFactory
        mock_client = MagicMock()
        factory = SandboxFactory(docker_client=mock_client)
        assert factory.client == mock_client

    def test_init_without_client(self):
        """Should create docker client from env when none provided."""
        with patch("backend.execution.sandbox_factory.docker.from_env") as mock_from_env:
            mock_client = MagicMock()
            mock_from_env.return_value = mock_client
            from backend.execution.sandbox_factory import SandboxFactory
            factory = SandboxFactory()
            assert factory.client == mock_client

    def test_create_sandbox_defaults(self):
        """create_sandbox should call docker with default parameters."""
        from backend.execution.sandbox_factory import SandboxFactory
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        factory = SandboxFactory(docker_client=mock_client)

        result = factory.create_sandbox("/tmp/testdir", binary_name="testprog")

        assert result == mock_container
        mock_client.containers.run.assert_called_once()
        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["network_mode"] == "none"
        assert call_kwargs["mem_limit"] == "128m"
        assert call_kwargs["cpu_quota"] == 50000
        assert call_kwargs["pids_limit"] == 64
        assert call_kwargs["read_only"] is True
        assert call_kwargs["user"] == "65534:65534"
        assert call_kwargs["stop_timeout"] == 12

    def test_create_sandbox_custom_params(self):
        """create_sandbox should accept custom security parameters."""
        from backend.execution.sandbox_factory import SandboxFactory
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        factory = SandboxFactory(docker_client=mock_client)

        result = factory.create_sandbox(
            "/tmp/testdir",
            binary_name="myprog",
            mem_limit="256m",
            cpu_quota=25000,
            pids_limit=32,
            stop_timeout=5,
        )

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["mem_limit"] == "256m"
        assert call_kwargs["cpu_quota"] == 25000
        assert call_kwargs["pids_limit"] == 32
        assert call_kwargs["stop_timeout"] == 5

    def test_destroy_sandbox_success(self):
        """destroy_sandbox should force-remove the container."""
        from backend.execution.sandbox_factory import SandboxFactory
        mock_client = MagicMock()
        factory = SandboxFactory(docker_client=mock_client)
        mock_container = MagicMock()
        mock_container.id = "abcdef123456"

        factory.destroy_sandbox(mock_container)
        mock_container.remove.assert_called_once_with(force=True)

    def test_destroy_sandbox_error(self):
        """destroy_sandbox should handle remove errors gracefully."""
        from backend.execution.sandbox_factory import SandboxFactory
        mock_client = MagicMock()
        factory = SandboxFactory(docker_client=mock_client)
        mock_container = MagicMock()
        mock_container.id = "abcdef123456"
        mock_container.remove.side_effect = Exception("Remove failed")

        # Should not raise
        factory.destroy_sandbox(mock_container)
        mock_container.remove.assert_called_once_with(force=True)
