"""Tests for WebSocket handler (ws_handler.py)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.ws_handler import (
    ConnectionState,
    WSState,
    _authenticate_ws,
    _handle_compile_and_run,
    _handle_stdin,
    _handle_stop,
    _safe_send,
)
from app.auth import AuthError
from tests.conftest import create_test_jwt


class TestConnectionState:
    """Tests for ConnectionState dataclass."""

    def test_initial_state(self):
        """Connection should start in IDLE state."""
        conn = ConnectionState()
        assert conn.state == WSState.IDLE
        assert conn.user_id is None
        assert conn.workdir is None
        assert conn._executor is None  # Lazy

    def test_state_transitions(self):
        """State should be mutable."""
        conn = ConnectionState()
        conn.state = WSState.COMPILING
        assert conn.state == WSState.COMPILING
        conn.state = WSState.EXECUTING
        assert conn.state == WSState.EXECUTING


class TestAuthenticateWS:
    """Tests for _authenticate_ws."""

    def test_valid_protocol_header(self, app, valid_jwt):
        """Authentication via Sec-WebSocket-Protocol should work."""
        with app.test_request_context(
            headers={"Sec-WebSocket-Protocol": f"bearer.{valid_jwt}"}
        ):
            conn = ConnectionState()
            _authenticate_ws(MagicMock(), conn)
            assert conn.user_id is not None

    def test_valid_query_token(self, app, valid_jwt):
        """Authentication via query param should work."""
        with app.test_request_context(query_string={"token": valid_jwt}):
            conn = ConnectionState()
            _authenticate_ws(MagicMock(), conn)
            assert conn.user_id is not None

    def test_missing_token(self, app):
        """Missing token should raise AuthError."""
        with app.test_request_context():
            conn = ConnectionState()
            with pytest.raises(AuthError):
                _authenticate_ws(MagicMock(), conn)

    def test_invalid_token(self, app):
        """Invalid token should raise AuthError."""
        with app.test_request_context(
            query_string={"token": "invalid-token"}
        ):
            conn = ConnectionState()
            with pytest.raises(AuthError):
                _authenticate_ws(MagicMock(), conn)


class TestHandleCompileAndRun:
    """Tests for _handle_compile_and_run."""

    def test_rejects_when_not_idle(self):
        """compile_and_run should be rejected if not in IDLE state."""
        conn = ConnectionState()
        conn.state = WSState.EXECUTING
        mock_ws = MagicMock()

        _handle_compile_and_run(mock_ws, conn, {"code": "programa t\ninicio\nfim"})

        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "internal_error"
        assert "currently" in sent["message"]

    def test_rejects_empty_code(self):
        """Empty code should send compile_error."""
        conn = ConnectionState()
        mock_ws = MagicMock()

        _handle_compile_and_run(mock_ws, conn, {"code": ""})

        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent["type"] == "compile_error"


class TestHandleStdin:
    """Tests for _handle_stdin."""

    def test_ignores_when_not_executing(self):
        """stdin in non-EXECUTING state should be ignored."""
        conn = ConnectionState()
        mock_ws = MagicMock()
        _handle_stdin(mock_ws, conn, {"data": "42\n"})
        mock_ws.send.assert_not_called()

    def test_logs_when_executing(self):
        """stdin in EXECUTING state should be logged (forwarding done by executor)."""
        conn = ConnectionState()
        conn.state = WSState.EXECUTING
        mock_ws = MagicMock()
        _handle_stdin(mock_ws, conn, {"data": "42\n"})
        mock_ws.send.assert_not_called()


class TestHandleStop:
    """Tests for _handle_stop."""

    def test_ignores_when_not_executing(self):
        """stop in non-EXECUTING state should be ignored."""
        conn = ConnectionState()
        conn.state = WSState.IDLE
        mock_ws = MagicMock()
        _handle_stop(mock_ws, conn)
        mock_ws.send.assert_not_called()

    def test_increments_counter_when_executing(self):
        """stop in EXECUTING state should increment counter."""
        from prometheus_client import REGISTRY
        before = REGISTRY.get_sample_value("simples_executions_stopped_total") or 0

        conn = ConnectionState()
        conn.state = WSState.EXECUTING
        mock_ws = MagicMock()
        _handle_stop(mock_ws, conn)

        after = REGISTRY.get_sample_value("simples_executions_stopped_total") or 0
        assert after == before + 1


class TestSafeSend:
    """Tests for _safe_send."""

    def test_sends_message(self):
        """_safe_send should send the message."""
        mock_ws = MagicMock()
        _safe_send(mock_ws, "hello")
        mock_ws.send.assert_called_once_with("hello")

    def test_handles_closed_connection(self):
        """_safe_send should not raise on ConnectionClosed."""
        from flask_sock import ConnectionClosed
        mock_ws = MagicMock()
        mock_ws.send.side_effect = ConnectionClosed()
        _safe_send(mock_ws, "hello")  # Should not raise
