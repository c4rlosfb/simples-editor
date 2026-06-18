"""Tests for execution/compiler_service.py."""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.execution.compiler_service import CompilerService


class TestCompilerServiceInit:
    """Tests for CompilerService.__init__."""

    def test_init_default(self):
        """Should create with default pty_strategy."""
        with patch("backend.execution.compiler_service.PtyExecutionStrategy") as mock_pty:
            svc = CompilerService()
            assert svc.pty_strategy is not None

    def test_init_custom_strategy(self):
        """Should accept custom pty_strategy."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)
        assert svc.pty_strategy == mock_strategy


class TestCompilerServiceCompile:
    """Tests for CompilerService.compile()."""

    def test_compile_success(self):
        """Full pipeline should succeed with mocked tools."""
        import shutil

        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("backend.execution.compiler_service.tempfile.mkdtemp", return_value=tmpdir):
                with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
                    # For simplesc call, write the .asm file
                    def side_effect(args, **kwargs):
                        # simplesc: [simplesc, source.simples, -o, output.asm]
                        # Only simplesc takes .simples input
                        has_simples = any(str(a).endswith(".simples") for a in args)
                        if has_simples:
                            out_idx = args.index("-o") + 1
                            asm_path = args[out_idx]
                            with open(asm_path, "w") as f:
                                f.write("section .text\nglobal _start\n_start:\n  mov eax, 1\n  int 0x80\n")
                        m = MagicMock()
                        m.returncode = 0
                        m.stdout = ""
                        m.stderr = ""
                        return m
                    mock_run.side_effect = side_effect

                    result = svc.compile("programa teste\ninicio\n  escreva 42\nfim\n")

                    assert result["success"] is True
                    assert "asm" in result
                    assert "binary_dir" in result
                    assert os.path.exists(result["binary_dir"])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_compile_simplesc_timeout(self):
        """simplesc timeout should return error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="simplesc", timeout=15)

            result = svc.compile("programa teste\ninicio\nfim\n")

            assert result["success"] is False
            assert len(result["errors"]) == 1
            assert "Tempo" in result["errors"][0]["message"]

    def test_compile_simplesc_not_found(self):
        """simplesc not found should return error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("simplesc not found")

            result = svc.compile("programa teste\ninicio\nfim\n")

            assert result["success"] is False
            assert "simplesc nao encontrado" in result["errors"][0]["message"]

    def test_compile_simplesc_error_with_parse(self):
        """simplesc returning non-zero should parse errors from stderr."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
            mock_simplesc = MagicMock()
            mock_simplesc.returncode = 1
            mock_simplesc.stdout = ""
            mock_simplesc.stderr = "4:7: caractere invalido '@'"
            mock_run.return_value = mock_simplesc

            result = svc.compile("programa teste\ninicio\n  @invalid\nfim\n")

            assert result["success"] is False
            assert len(result["errors"]) > 0

    def test_nasm_error(self):
        """NASM error should return error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("backend.execution.compiler_service.tempfile.mkdtemp", return_value=tmpdir):
                with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
                    call_count = [0]

                    def side_effect(args, **kwargs):
                        call_count[0] += 1
                        # simplesc call (has .simples input): write .asm and return success
                        has_simples = any(str(a).endswith(".simples") for a in args)
                        if has_simples:
                            out_idx = args.index("-o") + 1
                            asm_path = args[out_idx]
                            with open(asm_path, "w") as f:
                                f.write("section .text\n_start:\n")
                            m = MagicMock()
                            m.returncode = 0
                            m.stdout = ""
                            m.stderr = ""
                            return m
                        # nasm call (2nd call): raise error
                        if call_count[0] == 2:
                            raise subprocess.CalledProcessError(
                                returncode=1, cmd="nasm", output="",
                                stderr="NASM error: invalid instruction"
                            )
                        # ld call (3rd call): shouldn't reach here
                        m = MagicMock()
                        m.returncode = 0
                        m.stdout = ""
                        m.stderr = ""
                        return m
                    mock_run.side_effect = side_effect

                    result = svc.compile("programa teste\ninicio\nfim\n")

                    assert result["success"] is False
                    assert "NASM error" in result["errors"][0]["message"]
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_nasm_not_found(self):
        """NASM not found should return error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("backend.execution.compiler_service.tempfile.mkdtemp", return_value=tmpdir):
                with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
                    call_count = [0]

                    def side_effect(args, **kwargs):
                        call_count[0] += 1
                        has_simples = any(str(a).endswith(".simples") for a in args)
                        if has_simples:
                            out_idx = args.index("-o") + 1
                            asm_path = args[out_idx]
                            with open(asm_path, "w") as f:
                                f.write("section .text\n_start:\n")
                            m = MagicMock()
                            m.returncode = 0
                            m.stdout = ""
                            m.stderr = ""
                            return m
                        if call_count[0] == 2:
                            raise FileNotFoundError("nasm not found")
                        m = MagicMock()
                        m.returncode = 0
                        m.stdout = ""
                        m.stderr = ""
                        return m
                    mock_run.side_effect = side_effect

                    result = svc.compile("programa teste\ninicio\nfim\n")

                    assert result["success"] is False
                    assert "nasm nao encontrado" in result["errors"][0]["message"]
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_linker_error(self):
        """Linker error should return error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("backend.execution.compiler_service.tempfile.mkdtemp", return_value=tmpdir):
                with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
                    call_count = [0]

                    def side_effect(args, **kwargs):
                        call_count[0] += 1
                        has_simples = any(str(a).endswith(".simples") for a in args)
                        if has_simples:
                            out_idx = args.index("-o") + 1
                            asm_path = args[out_idx]
                            with open(asm_path, "w") as f:
                                f.write("section .text\n_start:\n")
                            m = MagicMock()
                            m.returncode = 0
                            m.stdout = ""
                            m.stderr = ""
                            return m
                        # nasm + ld: nasm is call 2, ld is call 3
                        if call_count[0] == 2:
                            # nasm succeeds
                            m = MagicMock()
                            m.returncode = 0
                            m.stdout = ""
                            m.stderr = ""
                            return m
                        # call 3 = ld, raise error
                        raise subprocess.CalledProcessError(
                            returncode=1, cmd="ld", output="",
                            stderr="Linker error: undefined reference"
                        )
                    mock_run.side_effect = side_effect

                    result = svc.compile("programa teste\ninicio\nfim\n")

                    assert result["success"] is False
                    assert "Linker error" in result["errors"][0]["message"]
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_linker_not_found(self):
        """Linker not found should return error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        tmpdir = tempfile.mkdtemp()
        try:
            with patch("backend.execution.compiler_service.tempfile.mkdtemp", return_value=tmpdir):
                with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
                    call_count = [0]

                    def side_effect(args, **kwargs):
                        call_count[0] += 1
                        has_simples = any(str(a).endswith(".simples") for a in args)
                        if has_simples:
                            out_idx = args.index("-o") + 1
                            asm_path = args[out_idx]
                            with open(asm_path, "w") as f:
                                f.write("section .text\n_start:\n")
                            m = MagicMock()
                            m.returncode = 0
                            m.stdout = ""
                            m.stderr = ""
                            return m
                        if call_count[0] == 2:
                            # nasm succeeds
                            m = MagicMock()
                            m.returncode = 0
                            m.stdout = ""
                            m.stderr = ""
                            return m
                        # call 3 = ld not found
                        raise FileNotFoundError("ld not found")
                    mock_run.side_effect = side_effect

                    result = svc.compile("programa teste\ninicio\nfim\n")

                    assert result["success"] is False
                    assert "Linker i686 nao encontrado" in result["errors"][0]["message"]
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_unexpected_exception(self):
        """Unexpected exception should be caught and reported."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        with patch("backend.execution.compiler_service.subprocess.run") as mock_run:
            mock_run.side_effect = RuntimeError("Something went terribly wrong")

            result = svc.compile("programa teste\ninicio\nfim\n")

            assert result["success"] is False
            assert "Erro" in result["errors"][0]["message"]


class TestCleanupBinaryDir:
    """Tests for cleanup_binary_dir()."""

    def test_cleanup_existing_dir(self):
        """Should remove existing directory."""
        import tempfile
        import shutil

        tmpdir = tempfile.mkdtemp()
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        svc.cleanup_binary_dir(tmpdir)
        assert not os.path.exists(tmpdir)

    def test_cleanup_nonexistent_dir(self):
        """Should not raise for nonexistent directory."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        svc.cleanup_binary_dir("/tmp/nonexistent-dir-xyz-12345")  # Should not raise

    def test_cleanup_none(self):
        """Should not raise for None."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        svc.cleanup_binary_dir(None)  # Should not raise


class TestParseErrors:
    """Tests for _parse_errors()."""

    def test_empty_stderr(self):
        """Empty stderr should return single generic error."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        errors = svc._parse_errors("")
        assert len(errors) >= 1

    def test_well_formed_error(self):
        """Well-formed error should be parsed correctly."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        errors = svc._parse_errors("4:7: caractere invalido")
        assert len(errors) == 1
        assert errors[0]["line"] == 4
        assert errors[0]["column"] == 7

    def test_partial_error(self):
        """Error with only line and message should work."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        errors = svc._parse_errors("10: variavel nao declarada")
        assert len(errors) == 1
        assert errors[0]["line"] == 10

    def test_non_numeric_line(self):
        """Non-numeric line should be handled gracefully."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        errors = svc._parse_errors("erro: algo deu errado")
        assert len(errors) >= 1

    def test_multiple_lines(self):
        """Multiple error lines should all be parsed."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        errors = svc._parse_errors("4:7: erro1\n8:5: erro2")
        assert len(errors) == 2

    def test_stderr_with_blank_lines(self):
        """Blank lines should be skipped."""
        mock_strategy = MagicMock()
        svc = CompilerService(pty_strategy=mock_strategy)

        errors = svc._parse_errors("\n  \n4:7: erro\n\n")
        assert len(errors) == 1
