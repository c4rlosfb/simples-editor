"""Testes para configuração do sandbox Docker com timeouts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sandbox_config import (
    TimeoutConfig,
    timeout_config,
    get_docker_run_args,
    get_docker_kill_sequence,
    validate_timeouts,
    COMPILE_TIMEOUT_S,
    EXEC_TIMEOUT_S,
    DOCKER_STOP_TIMEOUT_S,
    SIGTERM_GRACE_S,
)


class TestTimeoutConfig:
    def test_default_timeout_values(self):
        """Valores padrão devem corresponder ao PRD §11.3."""
        assert COMPILE_TIMEOUT_S == 15
        assert EXEC_TIMEOUT_S == 10
        assert DOCKER_STOP_TIMEOUT_S == 12
        assert SIGTERM_GRACE_S == 1

    def test_timeout_config_instance(self):
        """Instância padrão deve ter os valores do PRD."""
        assert timeout_config.compile_timeout_s == 15
        assert timeout_config.exec_timeout_s == 10
        assert timeout_config.docker_stop_timeout_s == 12

    def test_total_max_execution(self):
        """total_max_execution_s deve ser exec + grace + docker stop."""
        expected = 10 + 1 + 12  # 23s total máximo
        assert timeout_config.total_max_execution_s == expected

    def test_custom_timeout_config(self):
        """Config customizada deve permitir override."""
        custom = TimeoutConfig(
            compile_timeout_s=30,
            exec_timeout_s=20,
            docker_stop_timeout_s=15,
            sigterm_grace_s=2,
        )
        assert custom.compile_timeout_s == 30
        assert custom.total_max_execution_s == 20 + 2 + 15

    def test_config_is_immutable(self):
        """TimeoutConfig deve ser frozen (imutável)."""
        import dataclasses
        with __import__('pytest').raises(dataclasses.FrozenInstanceError):
            timeout_config.compile_timeout_s = 999  # type: ignore


class TestDockerArgs:
    def test_docker_run_args_includes_stop_timeout(self):
        """get_docker_run_args() deve incluir --stop-timeout."""
        args = get_docker_run_args()
        assert f"--stop-timeout={DOCKER_STOP_TIMEOUT_S}" in args

    def test_kill_sequence_order(self):
        """Sequência deve ser SIGTERM → espera → SIGKILL."""
        seq = get_docker_kill_sequence()
        assert len(seq) == 2
        assert seq[0][0] == "SIGTERM"
        assert seq[0][1] == SIGTERM_GRACE_S
        assert seq[1][0] == "SIGKILL"

    def test_kill_sequence_has_wait(self):
        """SIGTERM deve ter wait > 0 antes do SIGKILL."""
        seq = get_docker_kill_sequence()
        assert seq[0][1] > 0  # grace period

    def test_validate_timeouts(self):
        """validate_timeouts() não deve lançar exceção."""
        assert validate_timeouts() is True
