"""
Testes para o pipeline de compilação com timeouts.
"""

import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from pipeline import (
    run_pipeline,
    _run_stage,
    PipelineResult,
    StageResult,
    SIMPLESC_TIMEOUT,
    NASM_TIMEOUT,
    LD_TIMEOUT,
    MAX_CODE_BYTES,
)


class TestRunStage:
    """Testes para _run_stage()."""

    def test_successful_command(self, tmp_path):
        """Comando bem-sucedido deve retornar StageResult com success=True."""


        cmd = ["echo", "hello"] if platform.system() != "Windows" else ["cmd", "/c", "echo hello"]
        result = _run_stage(cmd, timeout=5, name="test", workdir=tmp_path)
        assert result.success
        assert "hello" in result.output
        assert result.duration_ms >= 0

    def test_failed_command(self, tmp_path):
        """Comando que falha deve retornar success=False."""
        result = _run_stage(
            ["false"], timeout=5, name="fail", workdir=tmp_path
        )
        # 'false' não existe no Windows — ajusta expectativa
        if result.timed_out:
            assert not result.success
        else:
            assert not result.success or result.exit_code != 0

    def test_timeout(self, tmp_path):
        """Comando que excede timeout deve retornar timed_out=True."""


        if platform.system() == "Windows":
            cmd = ["ping", "-n", "20", "127.0.0.1"]
        else:
            cmd = ["sleep", "10"]

        result = _run_stage(cmd, timeout=1, name="slow", workdir=tmp_path)
        assert not result.success
        assert result.timed_out


class TestPipelineResult:
    """Testes para as dataclasses."""

    def test_pipeline_result_defaults(self):
        result = PipelineResult(success=True)
        assert result.success
        assert result.asm == ""
        assert result.stages == []
        assert result.errors == []

    def test_stage_result_defaults(self):
        stage = StageResult(name="test", success=True)
        assert stage.name == "test"
        assert stage.success
        assert stage.timed_out is False


class TestRunPipeline:
    """Testes para run_pipeline()."""

    def test_empty_code_no_simplesc(self):
        """Código vazio sem simplesc deve retornar erro de ambiente."""
        result = run_pipeline("")
        assert not result.success
        # Se simplesc não está instalado, erro é de environment
        # Se está, erro é de compilação
        assert len(result.errors) > 0

    def test_oversized_code(self):
        """Código > 64KB deve ser rejeitado antes do pipeline."""
        big_code = "a" * (MAX_CODE_BYTES + 1)
        result = run_pipeline(big_code)
        assert not result.success
        assert any("64" in e["message"] or "KB" in e["message"] for e in result.errors)

    def test_code_at_limit_accepted(self):
        """Código exatamente em 64KB não deve ser rejeitado."""
        limit_code = "a" * MAX_CODE_BYTES
        result = run_pipeline(limit_code)
        # Não deve ter erro de validação de tamanho
        for e in result.errors:
            assert "64" not in e["message"].lower() or "KB" not in e["message"]


class TestTimeouts:
    """Testes específicos para timeouts do pipeline."""

    def test_timeout_constants(self):
        """Verifica que os timeouts estão configurados conforme PRD §11.3."""
        assert SIMPLESC_TIMEOUT == 15
        assert NASM_TIMEOUT == 15
        assert LD_TIMEOUT == 15

    def test_timeout_stage_result(self):
        """StageResult deve expor corretamente timed_out."""
        stage = StageResult(
            name="test",
            success=False,
            error="timeout",
            timed_out=True,
        )
        assert stage.timed_out
        assert not stage.success
