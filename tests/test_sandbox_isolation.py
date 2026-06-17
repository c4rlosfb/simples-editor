"""Testes para configuração de isolamento do sandbox Docker."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sandbox_isolation import (
    SandboxConfig,
    sandbox_config,
    SANDBOX_MEMORY,
    SANDBOX_CPUS,
    SANDBOX_PIDS_LIMIT,
    SANDBOX_USER,
)


class TestSandboxConfig:
    def test_default_config_values(self):
        """Valores padrão devem corresponder ao PRD §11.2."""
        assert sandbox_config.memory == "128m"
        assert sandbox_config.cpus == 0.5
        assert sandbox_config.pids_limit == 64
        assert sandbox_config.user == "65534:65534"
        assert sandbox_config.network_mode == "none"
        assert sandbox_config.read_only is True

    def test_config_is_immutable(self):
        """SandboxConfig deve ser frozen."""
        import dataclasses
        with __import__('pytest').raises(dataclasses.FrozenInstanceError):
            sandbox_config.memory = "256m"  # type: ignore

    def test_9_isolation_layers(self):
        """Deve ter exatamente 9 camadas de isolamento."""
        layers = sandbox_config.isolation_layers
        assert len(layers) == 9
        assert all(isinstance(l, str) for l in layers)

    def test_isolation_layers_content(self):
        """Cada camada deve documentar sua configuração."""
        layers = sandbox_config.isolation_layers
        assert any("network" in l.lower() for l in layers)
        assert any("memory" in l.lower() for l in layers)
        assert any("pids" in l.lower() or "pid" in l.lower() for l in layers)
        assert any("cap-drop" in l.lower() or "capabilities" in l.lower() for l in layers)

    def test_docker_create_args(self):
        """get_docker_create_args() deve retornar kwargs completos."""
        args = sandbox_config.get_docker_create_args("/tmp/test-programa")

        # Verifica campos essenciais
        assert args["network_mode"] == "none"
        assert args["mem_limit"] == "128m"
        assert args["pids_limit"] == 64
        assert args["read_only"] is True
        assert "ALL" in args["cap_drop"]
        assert args["user"] == "65534:65534"
        assert not args["remove"]  # removemos manualmente

    def test_docker_args_includes_binary_mount(self):
        """Deve montar o binário em modo read-only."""
        args = sandbox_config.get_docker_create_args("/tmp/my-binary")
        volumes = args["volumes"]
        assert "/tmp/my-binary" in volumes
        assert volumes["/tmp/my-binary"]["mode"] == "ro"

    def test_docker_args_includes_tmpfs(self):
        """Deve configurar tmpfs para /tmp."""
        args = sandbox_config.get_docker_create_args("/tmp/bin")
        assert "tmpfs" in args
        assert "/tmp" in args["tmpfs"]
        assert "8m" in args["tmpfs"]["/tmp"]

    def test_docker_args_no_stdin_open(self):
        """stdin_open deve ser True para leia."""
        args = sandbox_config.get_docker_create_args("/tmp/bin")
        assert args["stdin_open"] is True

    def test_custom_config(self):
        """Config customizada deve permitir override."""
        custom = SandboxConfig(
            memory="256m",
            cpus=1.0,
            pids_limit=128,
        )
        assert custom.memory == "256m"
        assert custom.cpus == 1.0
        assert custom.pids_limit == 128
        # Campos não sobrescritos mantêm default
        assert custom.network_mode == "none"
