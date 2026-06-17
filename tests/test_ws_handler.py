"""Testes para o WebSocket /ws/run e máquina de estados."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from ws_handler import (
    WSState,
    WSStateMachine,
    make_message,
    handle_compile_request,
    get_ws_protocol,
)


class TestWSState:
    def test_initial_state_is_idle(self):
        sm = WSStateMachine()
        assert sm.state == WSState.IDLE

    def test_can_compile_in_idle(self):
        sm = WSStateMachine()
        assert sm.can_compile()

    def test_cannot_compile_in_compiling(self):
        sm = WSStateMachine()
        sm.transition(WSState.COMPILING)
        assert not sm.can_compile()

    def test_cannot_compile_in_executing(self):
        sm = WSStateMachine()
        sm.transition(WSState.COMPILING)
        sm.transition(WSState.EXECUTING)
        assert not sm.can_compile()

    def test_can_stop_in_compiling(self):
        sm = WSStateMachine()
        sm.transition(WSState.COMPILING)
        assert sm.can_stop()

    def test_can_stop_in_executing(self):
        sm = WSStateMachine()
        sm.transition(WSState.COMPILING)
        sm.transition(WSState.EXECUTING)
        assert sm.can_stop()

    def test_cannot_stop_in_idle(self):
        sm = WSStateMachine()
        assert not sm.can_stop()

    def test_can_send_stdin_only_in_executing(self):
        sm = WSStateMachine()
        assert not sm.can_send_stdin()
        sm.transition(WSState.COMPILING)
        assert not sm.can_send_stdin()
        sm.transition(WSState.EXECUTING)
        assert sm.can_send_stdin()

    def test_full_lifecycle(self):
        """Ciclo completo: IDLE → COMPILING → EXECUTING → IDLE."""
        sm = WSStateMachine()
        assert sm.state == WSState.IDLE

        sm.transition(WSState.COMPILING)
        assert sm.state == WSState.COMPILING

        sm.transition(WSState.EXECUTING)
        assert sm.state == WSState.EXECUTING

        sm.transition(WSState.IDLE)
        assert sm.state == WSState.IDLE


class TestHandleCompileRequest:
    def test_valid_code_accepted(self):
        sm = WSStateMachine()
        error = handle_compile_request(sm, "programa teste\ninicio\nfim")
        assert error is None
        assert sm.state == WSState.COMPILING

    def test_empty_code_rejected(self):
        sm = WSStateMachine()
        error = handle_compile_request(sm, "")
        assert error is not None
        data = json.loads(error)
        assert data["type"] == "compile_error"
        assert "vazio" in data["message"].lower()

    def test_whitespace_only_rejected(self):
        sm = WSStateMachine()
        error = handle_compile_request(sm, "   \n  ")
        assert error is not None

    def test_oversized_code_rejected(self):
        sm = WSStateMachine()
        big_code = "a" * (64 * 1024 + 1)
        error = handle_compile_request(sm, big_code)
        assert error is not None
        data = json.loads(error)
        assert "KB" in data["message"] or "64" in data["message"]

    def test_rejects_in_compiling_state(self):
        sm = WSStateMachine()
        sm.transition(WSState.COMPILING)
        error = handle_compile_request(sm, "programa teste\ninicio\nfim")
        assert error is not None

    def test_rejects_in_executing_state(self):
        sm = WSStateMachine()
        sm.transition(WSState.COMPILING)
        sm.transition(WSState.EXECUTING)
        error = handle_compile_request(sm, "programa teste\ninicio\nfim")
        assert error is not None


class TestMakeMessage:
    def test_basic_message(self):
        msg = make_message("compile_started")
        data = json.loads(msg)
        assert data["type"] == "compile_started"

    def test_message_with_kwargs(self):
        msg = make_message("exit", code=0, duration_ms=42)
        data = json.loads(msg)
        assert data["type"] == "exit"
        assert data["code"] == 0
        assert data["duration_ms"] == 42

    def test_message_is_valid_json(self):
        msg = make_message("stdout", data="Hello\n")
        parsed = json.loads(msg)
        assert parsed["data"] == "Hello\n"


class TestGetProtocol:
    def test_protocol_has_required_fields(self):
        proto = get_ws_protocol()
        assert proto["endpoint"] == "/ws/run"
        assert "IDLE" in proto["states"]
        assert "compile_and_run" in proto["client_messages"]
        assert "stdout" in proto["server_messages"]
