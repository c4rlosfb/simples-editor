"""
WebSocket handler para /ws/run — fluxo de compilação e execução.

Implementa a máquina de estados (PRD §9.2.3):
  IDLE → COMPILING → EXECUTING → IDLE

Protocolo de mensagens (PRD §9.2.1-§9.2.2):
  Cliente → Servidor: compile_and_run, stdin, stop, ping
  Servidor → Cliente: compile_started, asm_generated, compile_error,
                       exec_started, stdout, stderr, exit, timeout, pong
"""

from __future__ import annotations

import json
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)


class WSState(Enum):
    """Estados da máquina de estados do WebSocket (PRD §9.2.3)."""
    IDLE = auto()
    COMPILING = auto()
    EXECUTING = auto()


# ── Protocol helpers ──────────────────────────────────────────


def make_message(msg_type: str, **kwargs) -> str:
    """Serializa uma mensagem do protocolo WebSocket."""
    return json.dumps({"type": msg_type, **kwargs})


# ── Message handlers ──────────────────────────────────────────


class WSStateMachine:
    """
    Máquina de estados por conexão WebSocket.

    Estados: IDLE, COMPILING, EXECUTING.
    Mensagens inválidas para o estado atual são descartadas com warning.
    """

    def __init__(self):
        self.state = WSState.IDLE

    def can_compile(self) -> bool:
        return self.state == WSState.IDLE

    def can_send_stdin(self) -> bool:
        return self.state == WSState.EXECUTING

    def can_stop(self) -> bool:
        return self.state in (WSState.COMPILING, WSState.EXECUTING)

    def transition(self, new_state: WSState) -> None:
        logger.debug("WS state: %s → %s", self.state.name, new_state.name)
        self.state = new_state


def handle_compile_request(sm: WSStateMachine, code: str) -> str | None:
    """
    Valida e inicia o fluxo de compilação.

    Returns:
        Mensagem de erro serializada se inválido, None se OK.
    """
    if not sm.can_compile():
        return make_message(
            "internal_error",
            message=f"Não é possível compilar no estado {sm.state.name}",
        )

    if not code or not code.strip():
        return make_message(
            "compile_error",
            phase="validation",
            line=0, column=0,
            message="Código vazio",
        )

    if len(code.encode("utf-8")) > 64 * 1024:
        return make_message(
            "compile_error",
            phase="validation",
            line=0, column=0,
            message="Código excede limite de 64 KB",
        )

    sm.transition(WSState.COMPILING)
    return None


def get_ws_protocol() -> dict:
    """
    Retorna a definição do protocolo WebSocket para documentação.

    Útil para health check e debugging.
    """
    return {
        "endpoint": "/ws/run",
        "states": ["IDLE", "COMPILING", "EXECUTING"],
        "client_messages": ["compile_and_run", "stdin", "stop", "ping"],
        "server_messages": [
            "compile_started", "compile_error", "asm_generated",
            "assemble_error", "link_error",
            "exec_started", "stdout", "stderr",
            "exit", "timeout", "internal_error", "pong",
        ],
    }
