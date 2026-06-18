"""Tests for app.execution.PtyExecutionStrategy — production execution module.

Tests the real PtyExecutionStrategy from app.execution (NOT the dead
backend.execution.pty_strategy). Uses app.execution.* for imports and patch paths.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.execution import ExecutionResult, PtyExecutionStrategy
from app.config import config


# ---------------------------------------------------------------------------
# PtyExecutionStrategy.__init__
# ---------------------------------------------------------------------------

class TestPtyExecutionStrategyInit:
    """Tests for PtyExecutionStrategy.__init__."""

    def test_init_default_image(self):
        """Should default to config.sandbox_image."""
        strategy = PtyExecutionStrategy()
        assert strategy.image == config.sandbox_image
        assert strategy._client is None  # lazy initialisation

    def test_init_custom_image(self):
        """Should accept an explicit image name."""
        strategy = PtyExecutionStrategy(image="custom-sandbox:v3")
        assert strategy.image == "custom-sandbox:v3"
        assert strategy._client is None

    @patch("app.execution.docker.from_env")
    def test_client_property_lazy_init(self, mock_from_env):
        """Accessing .client should trigger docker.from_env() exactly once."""
        strategy = PtyExecutionStrategy()
        assert strategy._client is None

        _ = strategy.client
        mock_from_env.assert_called_once()
        assert strategy._client is mock_from_env.return_value

        # Second access must NOT call from_env again
        _ = strategy.client
        mock_from_env.assert_called_once()


# ---------------------------------------------------------------------------
# PtyExecutionStrategy.execute()
# ---------------------------------------------------------------------------

class TestPtyExecutionStrategyExecute:
    """Tests for PtyExecutionStrategy.execute()."""

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _mock_docker_full(mock_from_env, *, recv_side_effect, wait_result=None):
        """Set up a complete mock Docker chain.

        Returns (mock_client, mock_container, mock_sock).
        """
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        if wait_result is not None:
            mock_container.wait.return_value = wait_result

        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock
        mock_sock._sock.recv.side_effect = recv_side_effect

        return mock_client, mock_container, mock_sock

    @staticmethod
    def _run_execute(strategy, *, ws=None, binary_dir=None, timeout_s=10,
                     stdin_queue=None, stop_event=None):
        """Run strategy.execute() synchronously on a fresh event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                strategy.execute(
                    binary_dir=binary_dir or MagicMock(),
                    ws=ws or AsyncMock(),
                    timeout_s=timeout_s,
                    stdin_queue=stdin_queue,
                    stop_event=stop_event,
                )
            )
        finally:
            loop.close()

    @staticmethod
    def _stop_event_set():
        ev = asyncio.Event()
        ev.set()
        return ev

    # -- container.run parameters -------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_container_run_sandbox_params(self, mock_from_env):
        """container.run should receive every security/sandbox parameter."""
        mock_client, mock_container, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy(image="sandbox:v2")
        self._run_execute(strategy, stop_event=self._stop_event_set())

        mock_client.containers.run.assert_called_once()
        kwargs = mock_client.containers.run.call_args[1]
        assert kwargs["image"] == "sandbox:v2"
        assert kwargs["command"] == ["/usr/bin/qemu-i386-static", "/sandbox/programa"]
        assert kwargs["network_mode"] == "none"
        assert kwargs["mem_limit"] == "128m"
        assert kwargs["memswap_limit"] == "128m"
        assert kwargs["cpu_quota"] == 50000
        assert kwargs["pids_limit"] == 64
        assert kwargs["read_only"] is True
        assert kwargs["tmpfs"] == {"/tmp": "size=8m"}
        assert kwargs["user"] == "65534:65534"
        assert kwargs["cap_drop"] == ["ALL"]
        assert kwargs["stdin_open"] is True
        assert kwargs["tty"] is True
        assert kwargs["detach"] is True
        # volumes: binds binary_dir → /sandbox ro
        assert "volumes" in kwargs

    # -- attach_socket ------------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_attach_socket_params(self, mock_from_env):
        """attach_socket should request stdin/stdout/stderr with stream=1."""
        _, mock_container, mock_sock = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy()
        self._run_execute(strategy, stop_event=self._stop_event_set())

        mock_container.attach_socket.assert_called_once_with(
            params={"stdin": 1, "stdout": 1, "stderr": 1, "stream": 1}
        )
        mock_sock._sock.setblocking.assert_called_once_with(False)

    # -- stdout forwarding --------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_stdout_forwarded_to_ws(self, mock_from_env):
        """Data read from the socket should be sent as JSON to the WebSocket."""
        _, _, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b"Hello World\n", b"Second line\n", b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy()
        mock_ws = AsyncMock()
        self._run_execute(strategy, ws=mock_ws, stop_event=self._stop_event_set())

        sent = [json.loads(c[0][0]) for c in mock_ws.send.call_args_list]
        stdout = [m for m in sent if m.get("type") == "stdout"]
        assert len(stdout) == 2
        assert stdout[0]["data"] == "Hello World\n"
        assert stdout[1]["data"] == "Second line\n"

    # -- stdin forwarding ---------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_stdin_forwarded_from_queue(self, mock_from_env):
        """stdin_queue entries should be forwarded to the container socket.

        NOTE: stop_event is NOT provided here. The production code checks
        stop_task before processing get_task (lines 151-153 of execution.py),
        so a pre-set stop_event would skip stdin forwarding. We rely on a
        short timeout to tear down the container after sendall is exercised.
        """
        _, _, mock_sock = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b"Prompt: ", b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy()
        mock_ws = AsyncMock()

        queue = asyncio.Queue()
        queue.put_nowait("42\n")

        result = self._run_execute(
            strategy,
            ws=mock_ws,
            stdin_queue=queue,
            timeout_s=0.1,
        )

        mock_sock._sock.sendall.assert_called_with(b"42\n")
        assert result.timed_out is True  # expected — nothing stops stdin_to_pty

    # -- stop event ---------------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_stop_event_kills_container(self, mock_from_env):
        """A set stop_event should cause container.kill('SIGTERM')."""
        _, mock_container, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 137},
        )

        strategy = PtyExecutionStrategy()
        self._run_execute(strategy, stop_event=self._stop_event_set())

        mock_container.kill.assert_called_with(signal="SIGTERM")

    # -- timeout ------------------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_execute_timeout(self, mock_from_env):
        """Short timeout should produce timed_out=True and call kill."""
        _, mock_container, _ = self._mock_docker_full(
            mock_from_env,
            # recv keeps returning data → pty_to_ws never finishes
            recv_side_effect=[b"x\n"] * 1000,
            wait_result={"StatusCode": -1},
        )

        strategy = PtyExecutionStrategy()
        result = self._run_execute(strategy, timeout_s=0.01)

        assert result.timed_out is True
        # SIGTERM first, then after 1 s sleep, SIGKILL
        assert mock_container.kill.call_count >= 1

    # -- image errors -------------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_image_not_found(self, mock_from_env):
        """ImageNotFound → internal_error message + exit_code=-1."""
        import docker.errors

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = docker.errors.ImageNotFound(
            "ghcr.io/.../simples-runner:latest not found"
        )

        strategy = PtyExecutionStrategy(image="simples-runner:latest")
        mock_ws = AsyncMock()
        result = self._run_execute(strategy, ws=mock_ws)

        assert result.exit_code == -1
        assert result.timed_out is False

        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "internal_error"
        assert "simples-runner:latest" in sent["message"]

    @patch("app.execution.docker.from_env")
    def test_docker_api_error(self, mock_from_env):
        """Docker APIError → internal_error + exit_code=-1."""
        import docker.errors

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = docker.errors.APIError(
            "Cannot connect to Docker daemon"
        )

        strategy = PtyExecutionStrategy()
        mock_ws = AsyncMock()
        result = self._run_execute(strategy, ws=mock_ws)

        assert result.exit_code == -1
        assert result.timed_out is False

        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "internal_error"

    # -- generic exception --------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_generic_exception(self, mock_from_env):
        """Any Exception during execution → exit_code=-1."""
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = RuntimeError("unknown failure")

        strategy = PtyExecutionStrategy()
        mock_ws = AsyncMock()
        result = self._run_execute(strategy, ws=mock_ws)

        assert result.exit_code == -1
        assert result.timed_out is False

        # Should still try to send an error message
        assert mock_ws.send.called

    # -- cleanup ------------------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_container_removed_on_success(self, mock_from_env):
        """Container should be force-removed even on success path."""
        _, mock_container, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy()
        self._run_execute(strategy, stop_event=self._stop_event_set())

        mock_container.remove.assert_called_once_with(force=True)

    @patch("app.execution.docker.from_env")
    def test_container_removed_on_error(self, mock_from_env):
        """Container should be force-removed even when ws.send explodes."""
        _, mock_container, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b"payload\n", b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy()
        mock_ws = AsyncMock()
        mock_ws.send.side_effect = ConnectionError("ws dead")

        self._run_execute(strategy, ws=mock_ws,
                          stop_event=self._stop_event_set())

        # finally block must still fire
        mock_container.remove.assert_called_once_with(force=True)

    @patch("app.execution.docker.from_env")
    def test_container_remove_error_suppressed(self, mock_from_env):
        """Failure to remove the container should not propagate."""
        _, mock_container, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 0},
        )
        mock_container.remove.side_effect = RuntimeError("remove failed")

        strategy = PtyExecutionStrategy()
        # Must not raise
        result = self._run_execute(strategy,
                                   stop_event=self._stop_event_set())
        assert result.exit_code == 0

    @patch("app.execution.docker.from_env")
    def test_no_container_to_remove(self, mock_from_env):
        """If container.run fails, finally block must not crash."""
        import docker.errors

        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        mock_client.containers.run.side_effect = docker.errors.ImageNotFound("nope")

        strategy = PtyExecutionStrategy()
        # container is None — finally must not reference it
        result = self._run_execute(strategy)
        assert result.exit_code == -1

    # -- result shape -------------------------------------------------------

    @patch("app.execution.docker.from_env")
    def test_result_exit_code_from_container(self, mock_from_env):
        """ExecutionResult.exit_code should come from container.wait."""
        _, _, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 42},
        )

        strategy = PtyExecutionStrategy()
        result = self._run_execute(strategy, stop_event=self._stop_event_set())
        assert result.exit_code == 42
        assert result.timed_out is False

    @patch("app.execution.docker.from_env")
    def test_result_includes_duration(self, mock_from_env):
        """ExecutionResult.duration_ms should be a non-negative integer."""
        _, _, _ = self._mock_docker_full(
            mock_from_env,
            recv_side_effect=[b""],
            wait_result={"StatusCode": 0},
        )

        strategy = PtyExecutionStrategy()
        result = self._run_execute(strategy, stop_event=self._stop_event_set())
        assert isinstance(result.duration_ms, int)
        assert result.duration_ms >= 0


# ---------------------------------------------------------------------------
# ExecutionResult dataclass
# ---------------------------------------------------------------------------

class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_fields_defaults(self):
        r = ExecutionResult(exit_code=0, duration_ms=100, timed_out=False)
        assert r.exit_code == 0
        assert r.duration_ms == 100
        assert r.timed_out is False

    def test_timeout_flag(self):
        r = ExecutionResult(exit_code=-1, duration_ms=5000, timed_out=True)
        assert r.timed_out is True

    def test_negative_exit_code(self):
        r = ExecutionResult(exit_code=-9, duration_ms=0, timed_out=False)
        assert r.exit_code == -9
