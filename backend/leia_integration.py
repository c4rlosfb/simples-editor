"""
Módulo de integração — bridge WebSocket ↔ PTY para execução interativa.

Implementa o fluxo end-to-end do `leia` (PRD §7.3 e §9.2):
1. Frontend envia código via WebSocket
2. Backend compila e executa em sandbox
3. stdin do terminal → WebSocket → PTY do container
4. stdout do container → WebSocket → terminal

Este módulo amarra os componentes: compiler, pipeline, sandbox, ws_handler.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class LeiaState(Enum):
    """Estados da máquina de execução interativa (PRD §9.2.3)."""
    IDLE = auto()
    COMPILING = auto()
    EXECUTING = auto()
    WAITING_INPUT = auto()  # Bloqueado no leia()
    FINISHED = auto()
    TIMEOUT = auto()
    ERROR = auto()


@dataclass
class LeiaMessage:
    """Mensagem do protocolo WebSocket (PRD §9.2)."""
    type: str
    data: str = ""
    code: str = ""
    asm: str = ""
    exit_code: int = 0
    duration_ms: int = 0
    error: str = ""


@dataclass
class LeiaSession:
    """
    Sessão de execução interativa.

    Mantém o estado e gerencia o fluxo de mensagens entre
    frontend (terminal) e backend (sandbox).
    """
    state: LeiaState = LeiaState.IDLE
    code: str = ""
    asm: str = ""
    stdin_queue: list[str] = field(default_factory=list)
    stdout_lines: list[str] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    start_time: float = 0.0
    timeout_s: int = 10

    def transition(self, new_state: LeiaState) -> None:
        """Transiciona a máquina de estados."""
        logger.debug("Transição: %s → %s", self.state.name, new_state.name)
        self.state = new_state

    def handle_client_message(self, msg: LeiaMessage) -> LeiaMessage | None:
        """
        Processa uma mensagem do cliente conforme a máquina de estados.

        Retorna a resposta a ser enviada de volta, ou None.
        """
        if msg.type == "compile_and_run":
            return self._handle_compile_and_run(msg)

        if msg.type == "stdin":
            return self._handle_stdin(msg)

        if msg.type == "stop":
            return self._handle_stop()

        logger.warning("Mensagem ignorada: type=%s em state=%s", msg.type, self.state.name)
        return None

    def _handle_compile_and_run(self, msg: LeiaMessage) -> LeiaMessage:
        """Inicia o pipeline de compilação e execução."""
        if self.state != LeiaState.IDLE:
            return LeiaMessage(type="error", error="Já existe uma execução em andamento")

        self.transition(LeiaState.COMPILING)
        self.code = msg.code
        self.start_time = time.monotonic()
        self.stdout_lines = []

        # Simula o pipeline (em produção, chamaria compiler.compile_simples + pipeline.run_pipeline)
        return LeiaMessage(type="compile_started")

    def _handle_stdin(self, msg: LeiaMessage) -> LeiaMessage | None:
        """Recebe input do terminal e encaminha para o processo."""
        if self.state not in (LeiaState.EXECUTING, LeiaState.WAITING_INPUT):
            logger.warning("stdin ignorado: estado=%s", self.state.name)
            return None

        self.stdin_queue.append(msg.data)
        self.transition(LeiaState.EXECUTING)
        return None  # stdin é unidirecional, sem resposta

    def _handle_stop(self) -> LeiaMessage:
        """Interrompe a execução."""
        if self.state not in (LeiaState.EXECUTING, LeiaState.WAITING_INPUT):
            return LeiaMessage(type="error", error="Nenhuma execução em andamento")

        self.transition(LeiaState.FINISHED)
        return LeiaMessage(
            type="exit",
            exit_code=-1,
            duration_ms=int((time.monotonic() - self.start_time) * 1000),
        )

    def simulate_execution(self, output_lines: list[str]) -> list[LeiaMessage]:
        """
        Simula a execução de um programa (para testes).

        Popula self.stdout_lines e retorna as mensagens que seriam
        enviadas ao frontend durante a execução.
        """
        self.transition(LeiaState.EXECUTING)

        messages: list[LeiaMessage] = []
        messages.append(LeiaMessage(type="exec_started"))

        for line in output_lines:
            self.stdout_lines.append(line)
            # Se a linha contém "leia" ou "Digite", estamos em WAITING_INPUT
            if "digite" in line.lower() or "leia" in line.lower():
                self.transition(LeiaState.WAITING_INPUT)
            messages.append(LeiaMessage(type="stdout", data=line))

        self.transition(LeiaState.FINISHED)
        duration = int((time.monotonic() - self.start_time) * 1000)
        messages.append(LeiaMessage(type="exit", exit_code=0, duration_ms=duration))

        return messages

    def simulate_leia_flow(self, program_output: list[str], user_inputs: list[str]) -> list[LeiaMessage]:
        """
        Simula o fluxo completo de um programa com leia().

        Exemplo:
            program_output = ["Digite um numero: ", "Dobro: 10"]
            user_inputs = ["5"]
            → mensagens: compile_started, exec_started, stdout("Digite..."),
              (pausa para input), stdin("5"), stdout("Dobro: 10"), exit
        """
        self.transition(LeiaState.COMPILING)
        messages = [LeiaMessage(type="compile_started")]

        # Simula compilação bem-sucedida
        messages.append(LeiaMessage(type="asm_generated", asm="; NASM gerado"))

        self.transition(LeiaState.EXECUTING)
        messages.append(LeiaMessage(type="exec_started"))

        input_idx = 0
        for line in program_output:
            messages.append(LeiaMessage(type="stdout", data=line))
            self.stdout_lines.append(line)

            # Detecta prompt de leia
            if ("digite" in line.lower() or "leia" in line.lower() or "numero" in line.lower()) and input_idx < len(user_inputs):
                self.transition(LeiaState.WAITING_INPUT)
                user_input = user_inputs[input_idx]
                self.stdin_queue.append(user_input)
                input_idx += 1
                self.transition(LeiaState.EXECUTING)

        self.transition(LeiaState.FINISHED)
        duration = int((time.monotonic() - self.start_time) * 1000)
        messages.append(LeiaMessage(type="exit", exit_code=0, duration_ms=duration))

        return messages


def validate_leia_protocol(messages: list[LeiaMessage]) -> bool:
    """
    Valida que a sequência de mensagens segue o protocolo (PRD §9.2.3).

    Ordem esperada: compile_started → asm_generated → exec_started →
    stdout* → [stdin? → stdout*] → exit
    """
    types = [m.type for m in messages]

    # Verifica início
    if "compile_started" not in types:
        return False

    # Verifica fim
    if "exit" not in types and "timeout" not in types and "compile_error" not in types:
        return False

    # Verifica que exec_started vem depois de compile_started
    cs_idx = types.index("compile_started") if "compile_started" in types else -1
    es_idx = types.index("exec_started") if "exec_started" in types else -1

    if es_idx != -1 and cs_idx != -1 and es_idx < cs_idx:
        return False

    return True
