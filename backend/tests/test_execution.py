"""Tests for execution strategies (execution.py)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.execution import PtyExecutionStrategy, CapturedExecutionStrategy, ExecutionResult
from app.config import config


class TestPtyExecutionStrategy:
    """Tests for PtyExecutionStrategy."""

    def test_init(self):
        """Strategy should initialize with default or custom image."""
        strategy = PtyExecutionStrategy()
        assert strategy.image == config.sandbox_image
        assert strategy._client is None  # Lazy init

        strategy = PtyExecutionStrategy(image="custom-runner:v2")
        assert strategy.image == "custom-runner:v2"
        assert strategy._client is None  # Still lazy

    @patch("app.execution.docker.from_env")
    def test_image_not_found(self, mock_from_env):
        """ImageNotFound should send internal_error and return exit_code -1."""
        import docker.errors

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = docker.errors.ImageNotFound(
            "simples-runner:latest not found"
        )

        strategy = PtyExecutionStrategy(image="simples-runner:latest")
        mock_ws = AsyncMock()

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            strategy.execute(
                binary_dir=MagicMock(),
                ws=mock_ws,
                timeout_s=10,
            )
        )
        loop.close()

        assert result.exit_code == -1
        assert result.timed_out is False
        calls = mock_ws.send.call_args_list
        sent = [json.loads(c[0][0]) for c in calls]
        internal_errors = [m for m in sent if m.get("type") == "internal_error"]
        assert len(internal_errors) > 0

    @patch("app.execution.docker.from_env")
    def test_docker_api_error(self, mock_from_env):
        """Docker APIError should be handled gracefully."""
        import docker.errors

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = docker.errors.APIError(
            "Cannot connect to Docker daemon"
        )

        strategy = PtyExecutionStrategy()
        mock_ws = AsyncMock()

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            strategy.execute(
                binary_dir=MagicMock(),
                ws=mock_ws,
                timeout_s=10,
            )
        )
        loop.close()

        assert result.exit_code == -1


class TestCapturedExecutionStrategy:
    """Tests for CapturedExecutionStrategy."""

    def test_execute_returns_not_implemented(self):
        """Captured strategy should return error for now."""
        strategy = CapturedExecutionStrategy()
        mock_ws = AsyncMock()

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            strategy.execute(
                binary_dir=MagicMock(),
                ws=mock_ws,
                timeout_s=10,
            )
        )
        loop.close()

        assert result.exit_code == -1
        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "internal_error"


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_creation(self):
        """ExecutionResult should store exit_code, duration, timeout."""
        result = ExecutionResult(exit_code=0, duration_ms=1234, timed_out=False)
        assert result.exit_code == 0
        assert result.duration_ms == 1234
        assert result.timed_out is False

    def test_timeout_result(self):
        """Timed-out execution should be captured correctly."""
        result = ExecutionResult(exit_code=-1, duration_ms=10000, timed_out=True)
        assert result.timed_out is True
        assert result.exit_code == -1
