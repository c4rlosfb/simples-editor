"""Tests for execution/pty_strategy.py."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestPtyExecutionStrategyInit:
    """Tests for PtyExecutionStrategy.__init__."""

    def test_init_default(self):
        """Should create with default sandbox factory."""
        with patch("backend.execution.pty_strategy.SandboxFactory") as mock_factory:
            from backend.execution.pty_strategy import PtyExecutionStrategy
            strategy = PtyExecutionStrategy()
            assert strategy.execution_timeout == 10
            assert strategy.sandbox_factory is not None

    def test_init_custom_client(self):
        """Should accept custom docker client."""
        mock_client = MagicMock()
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy(docker_client=mock_client, execution_timeout=30)
        assert strategy.execution_timeout == 30

    def test_init_custom_timeout(self):
        """Should accept custom execution timeout."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy(execution_timeout=60)
        assert strategy.execution_timeout == 60


class TestSendStdin:
    """Tests for send_stdin()."""

    def test_send_stdin_no_socket(self):
        """Should not raise when no socket is attached."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        # No socket yet - should not raise
        strategy.send_stdin(b"test")

    def test_send_stdin_with_socket(self):
        """Should write framed data to the socket."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_sock = MagicMock()
        strategy._sock = mock_sock

        strategy.send_stdin(b"42\n")
        mock_sock.write.assert_called_once()

    def test_send_stdin_socket_write_error(self):
        """Should handle socket write errors gracefully."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_sock = MagicMock()
        mock_sock.write.side_effect = Exception("Write failed")
        strategy._sock = mock_sock

        strategy.send_stdin(b"test")  # Should not raise


class TestStop:
    """Tests for stop()."""

    def test_stop_no_container(self):
        """Should not raise when no container."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        strategy.stop()  # Should not raise

    def test_stop_with_container(self):
        """Should send SIGTERM to container."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_container = MagicMock()
        strategy._container = mock_container

        strategy.stop()
        mock_container.kill.assert_called_once()

    def test_stop_container_kill_error(self):
        """Should handle kill errors gracefully."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_container = MagicMock()
        mock_container.kill.side_effect = Exception("Kill failed")
        strategy._container = mock_container

        strategy.stop()  # Should not raise


class TestReadSocket:
    """Tests for _read_socket()."""

    def test_read_socket_data(self):
        """Should return data when available."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_sock = MagicMock()
        mock_sock.fileno.return_value = 42

        with patch("backend.execution.pty_strategy.os.read", return_value=b"hello"):
            result = strategy._read_socket(mock_sock)
            assert result == b"hello"

    def test_read_socket_empty(self):
        """Should return None on empty read (EOF)."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_sock = MagicMock()
        mock_sock.fileno.return_value = 42

        with patch("backend.execution.pty_strategy.os.read", return_value=b""):
            result = strategy._read_socket(mock_sock)
            assert result is None

    def test_read_socket_error(self):
        """Should return None on OSError."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_sock = MagicMock()
        mock_sock.fileno.return_value = 42

        with patch("backend.execution.pty_strategy.os.read", side_effect=OSError):
            result = strategy._read_socket(mock_sock)
            assert result is None

    def test_read_socket_attribute_error(self):
        """Should return None on AttributeError."""
        from backend.execution.pty_strategy import PtyExecutionStrategy
        strategy = PtyExecutionStrategy()
        mock_sock = MagicMock()
        mock_sock.fileno.side_effect = AttributeError

        result = strategy._read_socket(mock_sock)
        assert result is None


class TestExecute:
    """Tests for execute() async generator."""

    def test_execute_success(self):
        """Execute should yield stdout and exit events on success."""
        from backend.execution.pty_strategy import PtyExecutionStrategy

        import asyncio

        mock_sandbox = MagicMock()
        mock_container = MagicMock()
        mock_container.attrs = {"State": {"ExitCode": 0}}
        mock_sandbox.create_sandbox.return_value = mock_container

        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock

        # Mock successful execution: read returns data then None
        read_calls = [b"output line\n", None]

        strategy = PtyExecutionStrategy()
        strategy.sandbox_factory = mock_sandbox

        with patch.object(strategy, "_read_socket", side_effect=read_calls):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def run():
                events = []
                async for event in strategy.execute("/tmp/test"):
                    events.append(event)
                return events

            events = loop.run_until_complete(run())
            loop.close()

            assert len(events) >= 2
            types = [e["type"] for e in events]
            assert "stdout" in types
            assert "exit" in types

    def test_execute_timeout(self):
        """Execute should yield timeout on asyncio.TimeoutError."""
        from backend.execution.pty_strategy import PtyExecutionStrategy

        mock_sandbox = MagicMock()
        mock_container = MagicMock()
        mock_container.attrs = {"State": {"ExitCode": -1}}
        mock_sandbox.create_sandbox.return_value = mock_container

        mock_sock = MagicMock()
        mock_container.attach_socket.return_value = mock_sock

        strategy = PtyExecutionStrategy(execution_timeout=0.01)
        strategy.sandbox_factory = mock_sandbox

        # Make _read_socket always raise BlockingIOError to trigger timeout
        with patch.object(strategy, "_read_socket", side_effect=BlockingIOError):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def run():
                events = []
                async for event in strategy.execute("/tmp/test"):
                    events.append(event)
                return events

            events = loop.run_until_complete(run())
            loop.close()

            types = [e["type"] for e in events]
            assert "timeout" in types

    def test_execute_docker_not_found(self):
        """Execute should yield error on docker.errors.NotFound."""
        import docker.errors
        from backend.execution.pty_strategy import PtyExecutionStrategy

        mock_sandbox = MagicMock()
        mock_sandbox.create_sandbox.side_effect = docker.errors.NotFound(
            "Image not found"
        )

        strategy = PtyExecutionStrategy()
        strategy.sandbox_factory = mock_sandbox

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            events = []
            async for event in strategy.execute("/tmp/test"):
                events.append(event)
            return events

        events = loop.run_until_complete(run())
        loop.close()

        assert any(e["type"] == "error" for e in events)

    def test_execute_docker_api_error(self):
        """Execute should yield error on docker.errors.APIError."""
        import docker.errors
        from backend.execution.pty_strategy import PtyExecutionStrategy

        mock_sandbox = MagicMock()
        mock_sandbox.create_sandbox.side_effect = docker.errors.APIError(
            "Docker daemon error"
        )

        strategy = PtyExecutionStrategy()
        strategy.sandbox_factory = mock_sandbox

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            events = []
            async for event in strategy.execute("/tmp/test"):
                events.append(event)
            return events

        events = loop.run_until_complete(run())
        loop.close()

        assert any(e["type"] == "error" for e in events)

    def test_execute_generic_exception(self):
        """Execute should yield error on generic Exception."""
        from backend.execution.pty_strategy import PtyExecutionStrategy

        mock_sandbox = MagicMock()
        mock_sandbox.create_sandbox.side_effect = RuntimeError("Something went wrong")

        strategy = PtyExecutionStrategy()
        strategy.sandbox_factory = mock_sandbox

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run():
            events = []
            async for event in strategy.execute("/tmp/test"):
                events.append(event)
            return events

        events = loop.run_until_complete(run())
        loop.close()

        assert any(e["type"] == "error" for e in events)
