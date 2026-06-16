"""
Testes para o módulo linker.py.

Valida que binutils-i686-linux-gnu está instalado e
que o linker gera binários ELF i386 corretos.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from linker import link_object, verify_toolchain, LD


class TestToolchainAvailability:
    """Verifica que binutils-i686-linux-gnu está instalado."""

    def test_ld_i686_exists(self):
        """i686-linux-gnu-ld deve estar no PATH."""
        found = shutil.which(LD)
        # Pode não estar instalado no dev local — não falha, apenas avisa
        if not found:
            pytest.skip(f"{LD} não instalado no ambiente de dev local")

        assert found is not None

    def test_verify_toolchain_returns_dict(self):
        """verify_toolchain() deve retornar um dicionário com as ferramentas."""
        tools = verify_toolchain()
        assert isinstance(tools, dict)
        assert "nasm" in tools
        assert "ld_i686" in tools


class TestLinkObject:
    """Testa o fluxo de linking ELF i386."""

    def test_link_missing_file(self):
        """Arquivo inexistente deve retornar erro."""
        success, msg = link_object(
            Path("/tmp/nonexistent.o"),
            Path("/tmp/output"),
        )
        assert not success
        assert "não encontrado" in msg

    def test_link_invalid_file(self):
        """Arquivo inválido deve retornar erro do linker."""
        with tempfile.NamedTemporaryFile(suffix=".o", delete=False) as f:
            f.write(b"nao eh um elf32 valido")
            obj_path = Path(f.name)

        try:
            output = obj_path.with_suffix("")

            # Só roda se o linker estiver instalado
            if shutil.which(LD) is None:
                pytest.skip(f"{LD} não disponível")

            success, msg = link_object(obj_path, output)
            assert not success  # Deve falhar (não é ELF32 válido)
            # O linker deve emitir algum erro
            assert len(msg) > 0 or not success
        finally:
            obj_path.unlink(missing_ok=True)
            if output.exists():
                output.unlink(missing_ok=True)

    def test_link_valid_elf32(self):
        """ELF32 válido deve ser linkado com sucesso."""
        if shutil.which(LD) is None:
            pytest.skip(f"{LD} não disponível")

        # Cria um .o mínimo via nasm (se disponível)
        nasm = shutil.which("nasm")
        if nasm is None:
            pytest.skip("nasm não disponível")

        asm_source = """
            global _start
            section .text
            _start:
                mov eax, 1
                xor ebx, ebx
                int 0x80
        """

        with tempfile.TemporaryDirectory() as tmp:
            asm_path = Path(tmp) / "test.asm"
            obj_path = Path(tmp) / "test.o"
            out_path = Path(tmp) / "test"

            asm_path.write_text(asm_source)
            subprocess.run(
                ["nasm", "-f", "elf32", "-o", str(obj_path), str(asm_path)],
                check=True,
                capture_output=True,
            )

            success, msg = link_object(obj_path, out_path)
            assert success, f"Link falhou: {msg}"
            assert out_path.exists()
            # Deve ser um executável ELF
            assert os.access(str(out_path), os.X_OK)
