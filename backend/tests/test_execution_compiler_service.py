"""Tests for app/compiler.py — CompilerService and CompileResult."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.compiler import CompilerService, CompileResult
from app.config import config
from app.errors import CompileError, parse_compile_errors


SAMPLE_CODE = "programa teste\ninicio\n  escreva 42\nfim\n"


class TestCompilerServiceInit:
    """Tests for CompilerService.__init__."""

    def test_init_default_paths(self):
        """Should initialize with default tool paths and tmp_base."""
        svc = CompilerService()
        assert svc.simplesc_path == "simplesc"
        assert svc.nasm_path == "nasm"
        assert svc.ld_path == "i686-linux-gnu-ld"
        assert svc.tmp_base is not None

    def test_init_custom_paths(self):
        """Should accept custom tool paths."""
        svc = CompilerService(
            simplesc_path="/opt/simplesc",
            nasm_path="/usr/local/bin/nasm",
            ld_path="/usr/bin/ld",
        )
        assert svc.simplesc_path == "/opt/simplesc"
        assert svc.nasm_path == "/usr/local/bin/nasm"
        assert svc.ld_path == "/usr/bin/ld"

    def test_init_custom_tmp_base(self):
        """Should accept custom tmp_base."""
        custom_tmp = Path("/custom/tmp")
        svc = CompilerService(tmp_base=custom_tmp)
        assert svc.tmp_base == custom_tmp


class TestCompilerServiceCompile:
    """Tests for CompilerService.compile()."""

    @patch("app.compiler.subprocess.run")
    def test_compile_success(self, mock_run):
        """Full pipeline (simplesc → nasm → ld) should succeed with mocked tools."""
        svc = CompilerService()

        # Mock three subprocess calls: simplesc, nasm, ld
        mock_simplesc = MagicMock(returncode=0, stdout="", stderr="")
        mock_nasm = MagicMock(returncode=0, stdout="", stderr="")
        mock_ld = MagicMock(returncode=0, stdout="", stderr="")
        mock_run.side_effect = [mock_simplesc, mock_nasm, mock_ld]

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)
            # Pre-create asm file so it can be "read" after mocked simplesc
            asm_path = workdir / "programa.asm"
            asm_path.write_text("section .text\nglobal _start\n_start:\n  mov eax, 1\n  int 0x80\n")

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is True
            assert result.asm_source is not None
            assert "section .text" in result.asm_source
            assert result.binary_dir == workdir
            assert result.duration_ms >= 0
            assert len(result.errors) == 0

    @patch("app.compiler.subprocess.run")
    def test_compile_simplesc_timeout(self, mock_run):
        """simplesc timeout should return error CompileResult."""
        svc = CompilerService()
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="simplesc", timeout=config.compile_timeout_s
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "timed out" in result.error_message.lower()
            assert result.duration_ms >= 0

    @patch("app.compiler.subprocess.run")
    def test_compile_simplesc_not_found(self, mock_run):
        """FileNotFoundError for simplesc should be caught and reported."""
        svc = CompilerService()
        fnf = FileNotFoundError()
        fnf.filename = "simplesc"
        mock_run.side_effect = fnf

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "not found" in result.error_message

    @patch("app.compiler.subprocess.run")
    def test_compile_simplesc_error_with_parse(self, mock_run):
        """simplesc returning non-zero should parse errors from stderr via parse_compile_errors."""
        svc = CompilerService()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "line 4, col 7: erro lexico: caractere invalido '@'\n"
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)

            result = svc.compile("programa teste\ninicio\n  @invalid\nfim\n", workdir=workdir)

            assert result.success is False
            assert len(result.errors) == 1
            assert isinstance(result.errors[0], CompileError)
            assert result.errors[0].line == 4
            assert result.errors[0].column == 7
            assert result.errors[0].phase == "lexer"

    @patch("app.compiler.subprocess.run")
    def test_compile_simplesc_error_no_parsed_errors(self, mock_run):
        """simplesc returning non-zero but no parseable stderr should report exit code."""
        svc = CompilerService()

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            # Should contain either exit code message or stderr fallback
            assert "exited with code 1" in (result.error_message or "")

    @patch("app.compiler.subprocess.run")
    def test_nasm_error(self, mock_run):
        """NASM CalledProcessError should be caught and reported."""
        svc = CompilerService()

        mock_simplesc = MagicMock(returncode=0, stdout="", stderr="")
        nasm_error = subprocess.CalledProcessError(
            returncode=1, cmd="nasm", output="", stderr="NASM error: invalid instruction"
        )
        mock_run.side_effect = [mock_simplesc, nasm_error]

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)
            # Pre-create asm for read after mocked simplesc
            (workdir / "programa.asm").write_text("section .text\n_start:\n")

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "NASM" in result.error_message

    @patch("app.compiler.subprocess.run")
    def test_nasm_not_found(self, mock_run):
        """NASM FileNotFoundError should be caught and reported."""
        svc = CompilerService()

        mock_simplesc = MagicMock(returncode=0, stdout="", stderr="")
        fnf = FileNotFoundError()
        fnf.filename = "nasm"
        mock_run.side_effect = [mock_simplesc, fnf]

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)
            (workdir / "programa.asm").write_text("section .text\n_start:\n")

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "not found" in result.error_message

    @patch("app.compiler.subprocess.run")
    def test_linker_error(self, mock_run):
        """Linker CalledProcessError should be caught and reported."""
        svc = CompilerService()

        mock_simplesc = MagicMock(returncode=0, stdout="", stderr="")
        mock_nasm = MagicMock(returncode=0, stdout="", stderr="")
        ld_error = subprocess.CalledProcessError(
            returncode=1, cmd="ld", output="", stderr="Linker error: undefined reference"
        )
        mock_run.side_effect = [mock_simplesc, mock_nasm, ld_error]

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)
            (workdir / "programa.asm").write_text("section .text\n_start:\n")

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "Linking" in result.error_message

    @patch("app.compiler.subprocess.run")
    def test_linker_not_found(self, mock_run):
        """Linker FileNotFoundError should be caught and reported."""
        svc = CompilerService()

        mock_simplesc = MagicMock(returncode=0, stdout="", stderr="")
        mock_nasm = MagicMock(returncode=0, stdout="", stderr="")
        fnf = FileNotFoundError()
        fnf.filename = "i686-linux-gnu-ld"
        mock_run.side_effect = [mock_simplesc, mock_nasm, fnf]

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)
            (workdir / "programa.asm").write_text("section .text\n_start:\n")

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "not found" in result.error_message

    @patch("app.compiler.subprocess.run")
    def test_unexpected_exception(self, mock_run):
        """Unexpected exception should be caught and reported."""
        svc = CompilerService()
        mock_run.side_effect = RuntimeError("Something went terribly wrong")

        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "work"
            workdir.mkdir(parents=True, exist_ok=True)

            result = svc.compile(SAMPLE_CODE, workdir=workdir)

            assert result.success is False
            assert result.error_message is not None
            assert "Unexpected" in result.error_message


class TestCleanup:
    """Tests for CompilerService.cleanup()."""

    def test_cleanup_existing_dir(self):
        """Should remove existing directory."""
        svc = CompilerService()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / "test.txt").write_text("test")

            svc.cleanup(test_dir)
            assert not test_dir.exists()

    def test_cleanup_nonexistent_dir(self):
        """Should not raise for nonexistent directory."""
        svc = CompilerService()
        svc.cleanup(Path("/tmp/nonexistent-dir-xyz-12345"))  # Should not raise

    def test_cleanup_exception_handled(self):
        """cleanup should not raise on rmtree failure (e.g. permission error)."""
        svc = CompilerService()
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "work"
            test_dir.mkdir(parents=True, exist_ok=True)

            with patch("app.compiler.shutil.rmtree", side_effect=Exception("Permission denied")):
                svc.cleanup(test_dir)  # Should not raise


class TestParseCompileErrors:
    """Tests for app.errors.parse_compile_errors()."""

    def test_empty_stderr(self):
        """Empty stderr should return empty list."""
        errors = parse_compile_errors("")
        assert len(errors) == 0

    def test_well_formed_error(self):
        """Well-formed lexer error should be parsed correctly."""
        errors = parse_compile_errors("line 4, col 7: erro lexico: caractere invalido")
        assert len(errors) == 1
        assert errors[0].line == 4
        assert errors[0].column == 7
        assert errors[0].phase == "lexer"
        assert "caractere invalido" in errors[0].message

    def test_well_formed_parser_error(self):
        """Well-formed parser error should be parsed correctly."""
        errors = parse_compile_errors("line 12, col 1: erro sintatico: esperado 'fim'")
        assert len(errors) == 1
        assert errors[0].line == 12
        assert errors[0].column == 1
        assert errors[0].phase == "parser"

    def test_well_formed_semantic_error(self):
        """Well-formed semantic error should be parsed correctly."""
        errors = parse_compile_errors("line 8, col 5: erro semantico: variavel nao declarada")
        assert len(errors) == 1
        assert errors[0].line == 8
        assert errors[0].column == 5
        assert errors[0].phase == "semantic"

    def test_generic_error_fallback(self):
        """Error without phase keyword should use generic fallback pattern."""
        errors = parse_compile_errors("line 10, col 1: variavel nao declarada")
        assert len(errors) == 1
        assert errors[0].line == 10
        assert errors[0].column == 1
        assert errors[0].phase == "unknown"

    def test_non_matching_line(self):
        """Non-matching line should be skipped gracefully (no match = no error)."""
        errors = parse_compile_errors("erro: algo deu errado")
        assert len(errors) == 0

    def test_multiple_lines(self):
        """Multiple error lines should all be parsed."""
        stderr = (
            "line 4, col 7: erro lexico: erro1\n"
            "line 8, col 5: erro sintatico: erro2\n"
        )
        errors = parse_compile_errors(stderr)
        assert len(errors) == 2
        assert errors[0].phase == "lexer"
        assert errors[1].phase == "parser"

    def test_stderr_with_blank_lines(self):
        """Blank lines should be skipped."""
        errors = parse_compile_errors("\n  \nline 4, col 7: erro lexico: erro\n\n")
        assert len(errors) == 1
