"""
Configuração de isolamento do sandbox Docker — 9 camadas de defesa.

PRD §11.2 — cada execução roda em container descartável com:
1. Container --rm
2. --network=none
3. --read-only + tmpfs:/tmp
4. --memory=128m --memory-swap=128m
5. --cpus=0.5
6. --pids-limit=64
7. --user=65534:65534 (nobody)
8. --cap-drop=ALL
9. Seccomp profile padrão Docker
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Constantes do sandbox (PRD §11.2)
SANDBOX_IMAGE = "simples-runner:latest"
SANDBOX_MEMORY = "128m"
SANDBOX_CPUS = 0.5
SANDBOX_PIDS_LIMIT = 64
SANDBOX_USER = "65534:65534"  # nobody
SANDBOX_TMPFS_SIZE = "8m"
SANDBOX_MOUNT_PATH = "/sandbox"
SANDBOX_RUNNER_COMMAND = "/usr/bin/qemu-i386-static"


@dataclass(frozen=True)
class SandboxConfig:
    """Configuração completa do sandbox com todas as camadas de isolamento."""

    image: str = SANDBOX_IMAGE
    memory: str = SANDBOX_MEMORY
    cpus: float = SANDBOX_CPUS
    pids_limit: int = SANDBOX_PIDS_LIMIT
    user: str = SANDBOX_USER
    tmpfs_size: str = SANDBOX_TMPFS_SIZE
    mount_path: str = SANDBOX_MOUNT_PATH
    runner_command: str = SANDBOX_RUNNER_COMMAND
    network_mode: str = "none"
    read_only: bool = True
    cap_drop: list[str] = field(default_factory=lambda: ["ALL"])

    @property
    def isolation_layers(self) -> list[str]:
        """Lista descritiva das 9 camadas de isolamento ativas."""
        return [
            f"1. Container criado sob demanda, destruído após execução",
            f"2. Network isolation (--network={self.network_mode})",
            f"3. Filesystem read-only + tmpfs:/tmp,size={self.tmpfs_size}",
            f"4. Memory limit (--memory={self.memory} --memory-swap={self.memory})",
            f"5. CPU limit (--cpus={self.cpus})",
            f"6. PID limit (--pids-limit={self.pids_limit})",
            f"7. Non-root user (--user={self.user})",
            f"8. Capabilities drop ({', '.join(f'--cap-drop={c}' for c in self.cap_drop)})",
            f"9. Seccomp profile (Docker default)",
        ]

    def get_docker_create_args(self, binary_path: str) -> dict:
        """
        Retorna kwargs para docker.containers.run().

        Args:
            binary_path: Caminho para o binário a ser executado no sandbox.

        Returns:
            Dicionário com todos os parâmetros de isolamento.
        """
        return {
            "image": self.image,
            "command": [self.runner_command, f"{self.mount_path}/programa"],
            "volumes": {
                binary_path: {
                    "bind": self.mount_path,
                    "mode": "ro",
                }
            },
            "network_mode": self.network_mode,
            "mem_limit": self.memory,
            "memswap_limit": self.memory,
            "cpu_quota": int(self.cpus * 100000),  # Docker SDK usa microsegundos
            "pids_limit": self.pids_limit,
            "read_only": self.read_only,
            "tmpfs": {"/tmp": f"size={self.tmpfs_size}"},
            "user": self.user,
            "cap_drop": self.cap_drop,
            "stdin_open": True,
            "tty": True,
            "detach": True,
            "remove": False,
        }


# Instância padrão
sandbox_config = SandboxConfig()
