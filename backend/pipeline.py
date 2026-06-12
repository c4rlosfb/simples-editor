"""
Pipeline de compilação com timeouts por estágio.

Orquestra: simplesc → nasm → ld
Cada estágio com timeout independente de 15s (PRD §11.3).
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# Timeouts por estágio (segundos) — PRD §11.3
SIMPLESC_TIMEOUT = 15
NASM_TIMEOUT = 15
LD_TIMEOUT = 15
MAX_CODE_BYTES = 64 * 1024


@dataclass
class StageResult:
    """Resultado de um estágio do pipeline."""
    name: str
    success: bool
    output: str = ""
    error: str = ""
    exit_code: int = -1
    duration_ms: float = 0
    timed_out: bool = False


@dataclass
class PipelineResult:
    """Resultado completo do pipeline de compilação."""
    success: bool
    asm: str = ""
    binary_path: str = ""
    stages: list[StageResult] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)


def _run_stage(cmd: list[str], timeout: int, name: str, workdir: Path) -> StageResult:
    """
    Executa um comando com timeout e captura stdout/stderr.

    Args:
        cmd: Comando e argumentos.
        timeout: Timeout em segundos.
        name: Nome do estágio para logging.
        workdir: Diretório de trabalho.

    Returns:
        StageResult com sucesso, saída e erro.
    """
    import time

    logger.debug("[%s] Executando: %s", name, " ".join(str(c) for c in cmd))
    start = time.monotonic()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(workdir),
        )
        duration = (time.monotonic() - start) * 1000

        return StageResult(
            name=name,
            success=result.returncode == 0,
            output=result.stdout.strip(),
            error=result.stderr.strip(),
            exit_code=result.returncode,
            duration_ms=round(duration, 2),
        )

    except subprocess.TimeoutExpired:
        duration = (time.monotonic() - start) * 1000
        logger.warning("[%s] Timeout após %.1fs", name, timeout)
        return StageResult(
            name=name,
            success=False,
            error=f"Estágio '{name}' excedeu timeout de {timeout}s",
            timed_out=True,
            duration_ms=round(duration, 2),
        )


def run_pipeline(code: str) -> PipelineResult:
    """
    Pipeline completo: simplesc → nasm → ld.

    Cada estágio tem timeout de 15s. Se qualquer estágio falhar,
    retorna o resultado parcial com os erros.

    Args:
        code: Código fonte SIMPLES.

    Returns:
        PipelineResult com assembly, binário (se sucesso) ou erros.
    """
    errors, stages = [], []

    # Validação de tamanho
    if len(code.encode("utf-8")) > MAX_CODE_BYTES:
        return PipelineResult(
            success=False,
            errors=[{
                "line": 0, "column": 0,
                "message": f"Código excede {MAX_CODE_BYTES // 1024} KB",
                "phase": "validation",
            }],
        )

    simplesc = shutil.which("simplesc")
    if not simplesc:
        logger.warning("simplesc não encontrado — pipeline indisponível")
        return PipelineResult(
            success=False,
            errors=[{
                "line": 0, "column": 0,
                "message": "simplesc não instalado no servidor",
                "phase": "environment",
            }],
        )

    with tempfile.TemporaryDirectory(prefix="simples-pipeline-") as tmp:
        tmpdir = Path(tmp)
        src = tmpdir / "programa.simples"
        asm_file = tmpdir / "programa.asm"
        obj_file = tmpdir / "programa.o"
        bin_file = tmpdir / "programa"

        src.write_text(code, encoding="utf-8")

        # --- Estágio 1: simplesc ---
        stage = _run_stage(
            [simplesc, str(src), "-o", str(asm_file)],
            timeout=SIMPLESC_TIMEOUT,
            name="simplesc",
            workdir=tmpdir,
        )
        stages.append(stage)

        if not stage.success:
            errors = _parse_pipeline_error(stage.error)
            return PipelineResult(success=False, stages=stages, errors=errors)

        asm = asm_file.read_text(encoding="utf-8") if asm_file.exists() else ""

        # --- Estágio 2: nasm ---
        stage = _run_stage(
            ["nasm", "-f", "elf32", "-o", str(obj_file), str(asm_file)],
            timeout=NASM_TIMEOUT,
            name="nasm",
            workdir=tmpdir,
        )
        stages.append(stage)

        if not stage.success:
            errors = _parse_pipeline_error(stage.error)
            return PipelineResult(
                success=False, asm=asm, stages=stages, errors=errors
            )

        # --- Estágio 3: ld ---
        stage = _run_stage(
            ["i686-linux-gnu-ld", "-m", "elf_i386", "-o", str(bin_file), str(obj_file)],
            timeout=LD_TIMEOUT,
            name="ld",
            workdir=tmpdir,
        )
        stages.append(stage)

        if not stage.success:
            errors = _parse_pipeline_error(stage.error)
            return PipelineResult(
                success=False, asm=asm, stages=stages, errors=errors
            )

        logger.info(
            "Pipeline concluído: simplesc=%.0fms nasm=%.0fms ld=%.0fms",
            stages[0].duration_ms,
            stages[1].duration_ms,
            stages[2].duration_ms,
        )

        return PipelineResult(
            success=True,
            asm=asm,
            binary_path=str(bin_file),
            stages=stages,
        )


def _parse_pipeline_error(stderr: str) -> list[dict]:
    """Parseia erros do pipeline em formato estruturado."""
    errors: list[dict] = []
    for line in stderr.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        error = {"line": 0, "column": 0, "message": line, "phase": "compiler"}

        parts = line.split(":", 2)
        try:
            error["line"] = int(parts[0].strip())
            if len(parts) >= 3:
                error["column"] = int(parts[1].strip())
                error["message"] = parts[2].strip()
            elif len(parts) == 2:
                error["message"] = parts[1].strip()
        except (ValueError, IndexError):
            pass

        errors.append(error)

    return errors
