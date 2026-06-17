"""
Módulo WebSocket — Protocol Events (Issue #34).

Implementa o endpoint WebSocket /ws/compile com flask-sock,
enviando eventos tipados para o frontend durante o pipeline
de compilação e execução.

Protocol Events:
  - compile_started → {type, timestamp}
  - asm_generated   → {type, asm, timestamp}
  - exec_started    → {type, timestamp}
  - stdout          → {type, data, timestamp}
  - exit            → {type, code, timestamp}
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from typing import Any

from flask import Flask
from flask_sock import Sock, Server

from leia_integration import (
    LeiaMessage,
    LeiaSession,
    LeiaState,
    validate_leia_protocol,
)

logger = logging.getLogger(__name__)


# ─── Protocol Events ─────────────────────────────────────────────────────────


@dataclass
class WsEvent:
    """Estrutura base para eventos do protocolo WebSocket."""

    type: str
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class CompileStartedEvent(WsEvent):
    type: str = "compile_started"


@dataclass
class AsmGeneratedEvent(WsEvent):
    type: str = "asm_generated"
    asm: str = ""


@dataclass
class ExecStartedEvent(WsEvent):
    type: str = "exec_started"


@dataclass
class StdoutEvent(WsEvent):
    type: str = "stdout"
    data: str = ""


@dataclass
class ExitEvent(WsEvent):
    type: str = "exit"
    code: int = 0


# ─── Event Factory ───────────────────────────────────────────────────────────


def make_event(
    event_type: str,
    **extra: Any,
) -> WsEvent:
    """Cria um evento tipado a partir de um type string e kwargs extras."""
    cls_map = {
        "compile_started": CompileStartedEvent,
        "asm_generated": AsmGeneratedEvent,
        "exec_started": ExecStartedEvent,
        "stdout": StdoutEvent,
        "exit": ExitEvent,
    }
    base_cls = cls_map.get(event_type, WsEvent)
    kwargs: dict[str, Any] = {"type": event_type, **extra}
    return base_cls(**{k: v for k, v in kwargs.items() if k in base_cls.__dataclass_fields__})


def send_event(ws: Server, event: WsEvent) -> None:
    """Serializa e envia um evento WebSocket."""
    payload = event.to_json()
    logger.debug("WS send: %s", payload[:200])
    ws.send(payload)


def send_error(ws: Server, message: str) -> None:
    """Envia um evento de erro."""
    payload = json.dumps({"type": "error", "message": message, "timestamp": time.time()})
    ws.send(payload)


# ─── Compilation Pipeline (mock/stub) ────────────────────────────────────────


def run_compile_pipeline(
    ws: Server,
    code: str,
    session: LeiaSession,
) -> None:
    """
    Executa o pipeline de compilação mockado, enviando eventos
    WebSocket para o cliente.

    Em produção, chamaria:
        1. compiler.compile_simples(code)
        2. pipeline.run_pipeline(asm)
        3. sandbox.execute(binary)
    """
    # 1. Compile started
    session.transition(LeiaState.COMPILING)
    send_event(ws, CompileStartedEvent())

    # Simula tempo de compilação
    time.sleep(0.05)

    # 2. ASM generated (simulado)
    mock_asm = (
        "; NASM x86 assembly gerado pelo compilador SIMPLES\n"
        "section .bss\n"
        "    _x resd 1\n"
        "section .text\n"
        "    global _start\n"
        "_start:\n"
        "    mov eax, 4\n"
        "    mov ebx, 1\n"
        "    mov ecx, _msg_hello\n"
        "    mov edx, 13\n"
        "    int 0x80\n"
        "    mov eax, 1\n"
        "    xor ebx, ebx\n"
        "    int 0x80\n"
        "section .data\n"
        "_msg_hello db 'Hello World!', 10\n"
    )
    session.asm = mock_asm
    send_event(ws, AsmGeneratedEvent(asm=mock_asm))

    # 3. Exec started
    session.transition(LeiaState.EXECUTING)
    send_event(ws, ExecStartedEvent())

    # 4. Simula saída (stdout)
    output_lines = ["Hello World!"]
    for line in output_lines:
        session.stdout_lines.append(line)
        send_event(ws, StdoutEvent(data=line))

    # 5. Exit
    session.transition(LeiaState.FINISHED)
    send_event(ws, ExitEvent(code=0))


# ─── WebSocket Handler ───────────────────────────────────────────────────────


def handle_compile_ws(ws: Server) -> None:
    """
    Handler principal do endpoint /ws/compile.

    Gerencia o ciclo de vida da conexão WebSocket:
    - Recebe mensagens do cliente (compile_and_run, stdin, stop)
    - Dispara o pipeline de compilação
    - Envia eventos de progresso
    """
    session = LeiaSession()
    logger.info("WS client connected")

    try:
        while True:
            raw = ws.receive()

            if raw is None:
                logger.info("WS client disconnected")
                break

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                send_error(ws, "Invalid JSON")
                continue

            msg_type = data.get("type", "")
            logger.debug("WS receive: %s", msg_type)

            if msg_type == "compile_and_run":
                code = data.get("code", "")
                if not code:
                    send_error(ws, "Missing 'code' field")
                    continue

                run_compile_pipeline(ws, code, session)

            elif msg_type == "stdin":
                stdin_data = data.get("data", "")
                msg = LeiaMessage(type="stdin", data=stdin_data)
                session.handle_client_message(msg)

            elif msg_type == "stop":
                msg = LeiaMessage(type="stop")
                response = session.handle_client_message(msg)
                if response:
                    code = getattr(response, "exit_code", -1)
                    send_event(ws, ExitEvent(code=code))
                break

            else:
                logger.warning("Unknown message type: %s", msg_type)
                send_error(ws, f"Unknown message type: {msg_type}")

    except Exception:
        logger.exception("Erro no WebSocket handler")
        try:
            send_event(ws, ExitEvent(code=-1))
        except Exception:
            pass


# ─── Flask Setup ─────────────────────────────────────────────────────────────


def register_websocket(app: Flask) -> Sock:
    """Registra o endpoint WebSocket /ws/compile em uma aplicação Flask existente.

    Uso:
        app = Flask(__name__)
        register_websocket(app)
    """
    app.config.setdefault("SOCK_SERVER_OPTIONS", {"ping_interval": 25})

    sock = Sock(app)

    @sock.route("/ws/compile")
    def compile_ws(ws: Server) -> None:
        handle_compile_ws(ws)

    return sock


def create_app() -> Flask:
    """
    Cria a aplicação Flask e registra o endpoint WebSocket.

    Uso:
        app = create_app()
        app.run(host='0.0.0.0', port=5000)
    """
    app = Flask(__name__)
    register_websocket(app)
    return app


# ─── CLI (para testes locais) ────────────────────────────────────────────────


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = create_app()
    logger.info("Starting WebSocket server on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
