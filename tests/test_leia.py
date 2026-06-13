"""
Testes end-to-end para o fluxo interativo leia().

Valida o protocolo WebSocket completo:
compilação → execução → stdin → stdout → exit
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from leia_integration import (
    LeiaState,
    LeiaMessage,
    LeiaSession,
    validate_leia_protocol,
)


class TestLeiaStateMachine:
    """Testes da máquina de estados (PRD §9.2.3)."""

    def test_initial_state_is_idle(self):
        session = LeiaSession()
        assert session.state == LeiaState.IDLE

    def test_compile_and_run_from_idle(self):
        session = LeiaSession()
        msg = LeiaMessage(type="compile_and_run", code="programa teste\ninicio\nfim")
        response = session.handle_client_message(msg)
        assert response is not None
        assert response.type == "compile_started"
        assert session.state == LeiaState.COMPILING

    def test_stdin_ignored_when_idle(self):
        session = LeiaSession()
        msg = LeiaMessage(type="stdin", data="hello\n")
        response = session.handle_client_message(msg)
        assert response is None  # Ignorado em IDLE

    def test_stdin_accepted_when_executing(self):
        session = LeiaSession()
        session.transition(LeiaState.EXECUTING)
        msg = LeiaMessage(type="stdin", data="42\n")
        response = session.handle_client_message(msg)
        assert response is None
        assert "42\n" in session.stdin_queue

    def test_stop_during_execution(self):
        session = LeiaSession()
        session.transition(LeiaState.EXECUTING)
        session.start_time = 0  # mock
        msg = LeiaMessage(type="stop")
        response = session.handle_client_message(msg)
        assert response is not None
        assert response.type == "exit"
        assert response.exit_code == -1
        assert session.state == LeiaState.FINISHED

    def test_stop_ignored_when_idle(self):
        session = LeiaSession()
        msg = LeiaMessage(type="stop")
        response = session.handle_client_message(msg)
        assert response is not None
        assert response.type == "error"

    def test_duplicate_compile_rejected(self):
        session = LeiaSession()
        session.transition(LeiaState.EXECUTING)
        msg = LeiaMessage(type="compile_and_run", code="programa x\ninicio\nfim")
        response = session.handle_client_message(msg)
        assert response is not None
        assert response.type == "error"
        assert "andamento" in response.error


class TestLeiaFlow:
    """Testes do fluxo completo com leia()."""

    def test_simulate_simple_execution(self):
        """Programa sem leia() deve gerar sequência limpa."""
        session = LeiaSession()
        output = ["Hello World", "Resultado: 42"]
        messages = session.simulate_execution(output)

        types = [m.type for m in messages]
        assert "exec_started" in types
        assert "exit" in types
        assert session.state == LeiaState.FINISHED

    def test_simulate_leia_program(self):
        """Programa com leia() deve passar por WAITING_INPUT."""
        session = LeiaSession()
        program_output = ["Digite um numero: ", "Dobro: 10"]
        user_inputs = ["5"]

        messages = session.simulate_leia_flow(program_output, user_inputs)

        types = [m.type for m in messages]
        assert "compile_started" in types
        assert "asm_generated" in types
        assert "exec_started" in types
        assert "exit" in types

        # Deve ter recebido o input
        assert len(session.stdin_queue) == 1
        assert session.stdin_queue[0] == "5"

        # Deve ter passado por WAITING_INPUT
        assert session.state == LeiaState.FINISHED

    def test_leia_with_multiple_inputs(self):
        """Programa com múltiplos leia()."""
        session = LeiaSession()
        program_output = [
            "Digite o primeiro numero: ",
            "Digite o segundo numero: ",
            "Soma: 30",
        ]
        user_inputs = ["10", "20"]

        messages = session.simulate_leia_flow(program_output, user_inputs)

        assert len(session.stdin_queue) == 2
        assert session.stdin_queue == ["10", "20"]

    def test_validate_protocol_valid(self):
        """Sequência válida deve passar na validação."""
        messages = [
            LeiaMessage(type="compile_started"),
            LeiaMessage(type="asm_generated", asm="; ok"),
            LeiaMessage(type="exec_started"),
            LeiaMessage(type="stdout", data="Digite um numero: "),
            LeiaMessage(type="exit", exit_code=0, duration_ms=100),
        ]
        assert validate_leia_protocol(messages) is True

    def test_validate_protocol_missing_start(self):
        """Sequência sem compile_started deve falhar."""
        messages = [
            LeiaMessage(type="exec_started"),
            LeiaMessage(type="exit"),
        ]
        assert validate_leia_protocol(messages) is False

    def test_validate_protocol_missing_end(self):
        """Sequência sem exit deve falhar."""
        messages = [
            LeiaMessage(type="compile_started"),
            LeiaMessage(type="exec_started"),
        ]
        assert validate_leia_protocol(messages) is False

    def test_validate_protocol_with_timeout(self):
        """Timeout no final também é válido."""
        messages = [
            LeiaMessage(type="compile_started"),
            LeiaMessage(type="asm_generated"),
            LeiaMessage(type="exec_started"),
            LeiaMessage(type="timeout"),
        ]
        assert validate_leia_protocol(messages) is True

    def test_messages_preserve_data(self):
        """Mensagens devem preservar os dados."""
        msg = LeiaMessage(
            type="stdout",
            data="Hello World",
            duration_ms=42,
        )
        assert msg.data == "Hello World"
        assert msg.duration_ms == 42


class TestLeiaIntegrationScenarios:
    """Cenários de integração realistas."""

    def test_fatorial_program_flow(self):
        """Simula o programa fatorial do PRD Apêndice A."""
        session = LeiaSession()
        session.code = """programa fatorial
  inteiro n, fat, contador
inicio
  leia n
  fat <- 1
  contador <- 1
  enquanto contador < n faca
    contador <- contador + 1
    fat <- fat * contador
  fimenquanto
  escreva fat
fim"""

        program_output = ["Digite um numero: ", "120"]
        user_inputs = ["5"]

        messages = session.simulate_leia_flow(program_output, user_inputs)

        assert session.state == LeiaState.FINISHED
        assert session.stdin_queue == ["5"]
        assert "120" in session.stdout_lines

    def test_soma_program_flow(self):
        """Simula programa de soma com dois leia()."""
        session = LeiaSession()

        program_output = [
            "Digite o primeiro valor: ",
            "Digite o segundo valor: ",
            "Resultado: 42",
        ]
        user_inputs = ["10", "32"]

        messages = session.simulate_leia_flow(program_output, user_inputs)

        assert session.state == LeiaState.FINISHED
        assert len(session.stdin_queue) == 2
        # Última mensagem deve ser exit
        assert messages[-1].type == "exit"
