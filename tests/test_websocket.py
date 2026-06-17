"""
Testes para o WebSocket Protocol Events (Issue #34).

Valida os eventos tipados e a estrutura do handler WebSocket.
"""

import json
import sys
import time
from pathlib import Path

# Adiciona o diretório backend ao path para importar o módulo
path = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.insert(0, path)

import pytest
from websocket_handler import (
    WsEvent,
    CompileStartedEvent,
    AsmGeneratedEvent,
    ExecStartedEvent,
    StdoutEvent,
    ExitEvent,
    make_event,
    send_event,
    send_error,
)


class TestWsEventStructure:
    """Testes da estrutura dos eventos WebSocket."""

    def test_compile_started_event(self):
        event = CompileStartedEvent()
        assert event.type == "compile_started"
        assert event.timestamp > 0

    def test_asm_generated_event(self):
        event = AsmGeneratedEvent(asm="; asm")
        assert event.type == "asm_generated"
        assert event.asm == "; asm"

    def test_exec_started_event(self):
        event = ExecStartedEvent()
        assert event.type == "exec_started"

    def test_stdout_event(self):
        event = StdoutEvent(data="output")
        assert event.type == "stdout"
        assert event.data == "output"

    def test_exit_event(self):
        event = ExitEvent(code=0)
        assert event.type == "exit"
        assert event.code == 0

    def test_exit_event_nonzero(self):
        event = ExitEvent(code=1)
        assert event.code == 1

    def test_json_serialization(self):
        event = CompileStartedEvent()
        payload = json.loads(event.to_json())
        assert payload["type"] == "compile_started"

    def test_json_with_asm(self):
        event = AsmGeneratedEvent(asm="; asm")
        payload = json.loads(event.to_json())
        assert payload["type"] == "asm_generated"
        assert "asm" in payload

    def test_json_with_stdout(self):
        event = StdoutEvent(data="output")
        payload = json.loads(event.to_json())
        assert payload["type"] == "stdout"
        assert "data" in payload

    def test_json_with_exit_code(self):
        event = ExitEvent(code=42)
        payload = json.loads(event.to_json())
        assert payload["type"] == "exit"
        assert payload["code"] == 42

    def test_timestamp_auto_generated(self):
        before = time.time()
        event = CompileStartedEvent()
        after = time.time()
        assert before <= event.timestamp <= after

    def test_timestamp_custom(self):
        event = CompileStartedEvent(timestamp=123.456)
        assert event.timestamp == 123.456

    def test_make_event_factory(self):
        event = make_event("compile_started")
        assert isinstance(event, CompileStartedEvent)
        assert event.type == "compile_started"


class TestWsEventSequence:
    """Testes da sequência de eventos do pipeline."""

    def test_compile_types(self):
        events = [
            CompileStartedEvent(),
            AsmGeneratedEvent(asm="; asm"),
            ExecStartedEvent(),
            StdoutEvent(data="output"),
            ExitEvent(code=0),
        ]
        types = [e.type for e in events]
        assert types == ["compile_started", "asm_generated", "exec_started", "stdout", "exit"]

    def test_compile_sequence_has_timestamps(self):
        events = [
            CompileStartedEvent(),
            AsmGeneratedEvent(asm="; asm"),
            ExecStartedEvent(),
            StdoutEvent(data="output"),
            ExitEvent(code=0),
        ]
        for event in events:
            assert event.timestamp > 0, f"{event.type} missing timestamp"

    def test_compile_sequence_timestamps_increasing(self):
        events = [
            CompileStartedEvent(),
            AsmGeneratedEvent(asm="; asm"),
            ExecStartedEvent(),
            StdoutEvent(data="output"),
            ExitEvent(code=0),
        ]
        for i in range(1, len(events)):
            assert events[i].timestamp >= events[i - 1].timestamp, \
                f"Timestamp decreased at index {i}"


class TestWsErrorEvent:
    """Testes do evento de erro."""

    def test_error_event(self):
        error_payload = json.dumps({
            "type": "error",
            "message": "Invalid JSON",
            "timestamp": time.time(),
        })
        parsed = json.loads(error_payload)
        assert parsed["type"] == "error"
        assert parsed["message"] == "Invalid JSON"
        assert "timestamp" in parsed
