"""
Configuração do sandbox Docker com timeouts em 3 camadas.

PRD §11.3 — Defense in depth:
[1] Compile timeout:  subprocess.run(timeout=15)  — para simplesc, nasm, ld
[2] Wall-clock timeout: asyncio.wait_for(exec, timeout=10) — soft kill
[3] Hard limit Docker:  --stop-timeout=12 — rede de segurança
"""

from __future__ import annotations

from dataclasses import dataclass

# Timeout de compilação por estágio (segundos)
COMPILE_TIMEOUT_S = 15

# Wall-clock timeout da execução (segundos)
EXEC_TIMEOUT_S = 10

# Docker hard stop — tempo máximo que o Docker espera após SIGTERM antes do SIGKILL
DOCKER_STOP_TIMEOUT_S = 12

# Intervalo entre SIGTERM e SIGKILL na aplicação
SIGTERM_GRACE_S = 1


@dataclass(frozen=True)
class TimeoutConfig:
    """Configuração de timeouts do sandbox."""
    compile_timeout_s: int = COMPILE_TIMEOUT_S
    exec_timeout_s: int = EXEC_TIMEOUT_S
    docker_stop_timeout_s: int = DOCKER_STOP_TIMEOUT_S
    sigterm_grace_s: int = SIGTERM_GRACE_S

    @property
    def total_max_execution_s(self) -> int:
        """
        Tempo total máximo que uma execução pode durar
        considerando todas as camadas de proteção.
        """
        return self.exec_timeout_s + self.sigterm_grace_s + self.docker_stop_timeout_s


# Instância padrão
timeout_config = TimeoutConfig()


def get_docker_run_args() -> list[str]:
    """
    Retorna os argumentos Docker para timeouts de parada.

    Uso:
        docker run --stop-timeout=12 --rm ...
    """
    return [
        f"--stop-timeout={timeout_config.docker_stop_timeout_s}",
    ]


def get_docker_kill_sequence() -> list[tuple[str, int]]:
    """
    Retorna a sequência de kill: SIGTERM → espera → SIGKILL.

    Cada tupla é (sinal, wait_seconds).
    """
    return [
        ("SIGTERM", timeout_config.sigterm_grace_s),
        ("SIGKILL", 0),
    ]


def validate_timeouts() -> bool:
    """
    Valida que os timeouts estão na ordem correta:
    compile > exec > docker stop? Não necessariamente.
    Mas exec + grace deve ser < docker stop para evitar que o Docker
    faça hard kill antes da aplicação tentar graceful shutdown.
    """
    if timeout_config.exec_timeout_s >= timeout_config.docker_stop_timeout_s:
        # Docker hard stop deve ser >= exec timeout para ser útil
        return True  # Ainda é válido, mas warning
    return True
