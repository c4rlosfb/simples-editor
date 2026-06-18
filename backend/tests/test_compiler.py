"""Tests for compiler service (compiler.py)."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.compiler import CompilerService, CompileResult
from app.config import config


SAMPLE_SIMPLES_CODE = """programa fatorial
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


class TestCompilerService:
    """Tests for CompilerService."""

    def test_init_defaults(self):
        """CompilerService should initialize with sensible defaults."""
        svc = CompilerService()
        assert svc.simplesc_path == "simplesc"
        assert svc.nasm_path == "nasm"
        assert svc.ld_path == "i686-linux-gnu-ld"

    def test_init_custom_paths(self):
        """CompilerService should accept custom tool paths."""
        svc = CompilerService(
            simplesc_path="/opt/simplesc",
            nasm_path="/usr/local/bin/nasm",
            ld_path="/usr/bin/i686-linux-gnu-ld",
        )
        assert svc.simplesc_path == "/opt/simplesc"

    @patch("app.compiler.subprocess.run")
    def test_successful_compilation(self, mock_run):
        """Full compilation pipeline should succeed with mocked tools."""
        svc = CompilerService()

        # Mock returns for each step
        mock_simplesc = MagicMock()
        mock_simplesc.returncode = 0
        mock_simplesc.stdout = ""
        mock_simplesc.stderr = ""

        mock_nasm = MagicMock()
        mock_nasm.returncode = 0
        mock_nasm.stdout = ""
        mock_nasm.stderr = ""

        mock_ld = MagicMock()
        mock_ld.returncode = 0
        mock_ld.stdout = ""
        mock_ld.stderr = ""

        mock_run.side_effect = [mock_simplesc, mock_nasm, mock_ld]

        # Create a real temp directory for workdir
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)

            # Write a dummy asm file so _run_simplesc can "read" it
            asm_file = test_dir / "programa.asm"
            asm_file.write_text("section .text\nglobal _start\n_start:\n")
            (test_dir / "programa.simples").write_text(SAMPLE_SIMPLES_CODE)

            result = svc.compile(SAMPLE_SIMPLES_CODE, workdir=test_dir)

            assert result.success is True
            assert result.asm_source is not None
            assert "section .text" in result.asm_source
            assert result.binary_dir == test_dir
            assert result.duration_ms >= 0

    @patch("app.compiler.subprocess.run")
    def test_compile_error_parsing(self, mock_run):
        """Compile errors from simplesc should be parsed."""
        svc = CompilerService()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "line 4, col 7: erro lexico: caractere invalido '@'\n"
        mock_run.return_value = mock_result

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text("programa teste\ninicio\n  @invalid\nfim")

            result = svc.compile("programa teste\ninicio\n  @invalid\nfim", workdir=test_dir)
            assert result.success is False
            assert len(result.errors) == 1
            assert result.errors[0].phase == "lexer"
            assert result.errors[0].line == 4

    @patch("app.compiler.subprocess.run")
    def test_timeout_handling(self, mock_run):
        """TimeoutExpired should be caught and returned as CompileResult."""
        svc = CompilerService()
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="simplesc", timeout=config.compile_timeout_s
        )

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text(SAMPLE_SIMPLES_CODE)

            result = svc.compile(SAMPLE_SIMPLES_CODE, workdir=test_dir)
            assert result.success is False
            assert result.error_message is not None
            assert "timed out" in result.error_message.lower()

    @patch("app.compiler.subprocess.run")
    def test_tool_not_found(self, mock_run):
        """FileNotFoundError should be caught and reported."""
        svc = CompilerService()
        mock_run.side_effect = FileNotFoundError("simplesc not found")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text(SAMPLE_SIMPLES_CODE)

            result = svc.compile(SAMPLE_SIMPLES_CODE, workdir=test_dir)
            assert result.success is False
            assert result.error_message is not None

    def test_cleanup(self):
        """cleanup should remove the workdir without errors."""
        svc = CompilerService()
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "test.txt").write_text("hello")

            svc.cleanup(test_dir)
            assert not test_dir.exists()

    def test_cleanup_nonexistent(self):
        """cleanup should not raise on non-existent paths."""
        svc = CompilerService()
        svc.cleanup(Path("/tmp/nonexistent-path-12345"))  # Should not raise

    def test_create_workdir(self):
        """_create_workdir should create a unique directory."""
        import tempfile
        tmp_base = Path(tempfile.mkdtemp())
        try:
            svc = CompilerService(tmp_base=tmp_base)
            d1 = svc._create_workdir()
            d2 = svc._create_workdir()
            assert d1.exists()
            assert d2.exists()
            assert d1 != d2
            svc.cleanup(d1)
            svc.cleanup(d2)
        finally:
            import shutil
            shutil.rmtree(tmp_base, ignore_errors=True)

    @patch("app.compiler.subprocess.run")
    def test_nasm_error(self, mock_run):
        """NASM CalledProcessError should be caught."""
        svc = CompilerService()
        mock_simplesc = MagicMock()
        mock_simplesc.returncode = 0
        mock_simplesc.stdout = ""
        mock_simplesc.stderr = ""

        nasm_error = subprocess.CalledProcessError(
            returncode=1, cmd="nasm", output="", stderr="NASM error"
        )
        mock_run.side_effect = [mock_simplesc, nasm_error]

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text(SAMPLE_SIMPLES_CODE)
            asm_file = test_dir / "programa.asm"
            asm_file.write_text("section .text\nglobal _start\n_start:\n")

            result = svc.compile(SAMPLE_SIMPLES_CODE, workdir=test_dir)
            assert result.success is False
            assert "NASM" in (result.error_message or "")

    @patch("app.compiler.subprocess.run")
    def test_ld_error(self, mock_run):
        """LD CalledProcessError should be caught."""
        svc = CompilerService()
        mock_simplesc = MagicMock()
        mock_simplesc.returncode = 0
        mock_simplesc.stdout = ""
        mock_simplesc.stderr = ""

        mock_nasm = MagicMock()
        mock_nasm.returncode = 0
        mock_nasm.stdout = ""
        mock_nasm.stderr = ""

        ld_error = subprocess.CalledProcessError(
            returncode=1, cmd="ld", output="", stderr="Linking failed"
        )
        mock_run.side_effect = [mock_simplesc, mock_nasm, ld_error]

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text(SAMPLE_SIMPLES_CODE)
            asm_file = test_dir / "programa.asm"
            asm_file.write_text("section .text\nglobal _start\n_start:\n")

            result = svc.compile(SAMPLE_SIMPLES_CODE, workdir=test_dir)
            assert result.success is False
            assert "Linking" in (result.error_message or "")

    @patch("app.compiler.subprocess.run")
    def test_simplesc_error_no_parsed_errors(self, mock_run):
        """simplesc returning non-zero but no parseable errors should use exit code message."""
        svc = CompilerService()
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text("programa t\ninicio\nfim\n")

            result = svc.compile("programa t\ninicio\nfim\n", workdir=test_dir)
            assert result.success is False
            assert result.error_message is not None

    @patch("app.compiler.subprocess.run")
    def test_generic_exception_handling(self, mock_run):
        """Generic Exception in compile should be caught and reported."""
        svc = CompilerService()
        mock_run.side_effect = RuntimeError("Something unexpected")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "programa.simples").write_text(SAMPLE_SIMPLES_CODE)

            result = svc.compile(SAMPLE_SIMPLES_CODE, workdir=test_dir)
            assert result.success is False
            assert result.error_message is not None
            assert "Unexpected" in result.error_message

    @patch("app.compiler.shutil.which")
    def test_compile_simples_mock_fallback(self, mock_which):
        """compile_simples should return mock result when simplesc not available."""
        from app.compiler import compile_simples
        mock_which.return_value = None  # simplesc not found

        result = compile_simples("programa t\ninicio\n  escreva 1\nfim\n")
        assert result.success is True
        assert result.asm_source is not None
        assert "; SIMPLES → NASM (mock" in result.asm_source

    @patch("app.compiler.CompilerService.compile")
    @patch("app.compiler.shutil.which")
    def test_compile_simples_real(self, mock_which, mock_compile):
        """compile_simples should use real compiler when available."""
        from app.compiler import compile_simples, CompileResult
        mock_which.return_value = "/usr/bin/simplesc"
        expected = CompileResult(success=True, asm_source="real asm")
        mock_compile.return_value = expected

        result = compile_simples("programa t\ninicio\nfim\n")
        assert result.success is True
        assert result.asm_source == "real asm"

    def test_cleanup_exception_handling(self):
        """cleanup should not raise on permission errors."""
        svc = CompilerService()
        import tempfile
        tmpdir = Path(tempfile.mkdtemp())
        test_dir = tmpdir / "work"
        test_dir.mkdir(parents=True, exist_ok=True)

        with patch("app.compiler.shutil.rmtree", side_effect=Exception("Perm denied")):
            svc.cleanup(test_dir)  # Should not raise
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
