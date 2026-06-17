"""Compiler service — Facade over the simplesc → nasm → ld pipeline.

Implements the Facade pattern described in PRD §7.4.
Handles the full compilation pipeline detailed in PRD §7.3 (steps 3-6).
"""

import logging
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.config import config
from app.errors import CompileError, parse_compile_errors

logger = logging.getLogger("simples.compiler")


@dataclass
class CompileResult:
    """Result of a compilation pipeline run."""

    success: bool
    asm_source: Optional[str] = None
    binary_dir: Optional[Path] = None
    errors: list[CompileError] = field(default_factory=list)
    error_message: Optional[str] = None
    duration_ms: int = 0


class CompilerService:
    """Facade that orchestrates simplesc → nasm → ld."""

    def __init__(
        self,
        simplesc_path: str = "simplesc",
        nasm_path: str = "nasm",
        ld_path: str = "i686-linux-gnu-ld",
        tmp_base: Optional[Path] = None,
    ):
        self.simplesc_path = simplesc_path
        self.nasm_path = nasm_path
        self.ld_path = ld_path
        self.tmp_base = tmp_base or config.tmp_base

    def compile(self, code: str, workdir: Optional[Path] = None) -> CompileResult:
        """Run the full compilation pipeline: simplesc → nasm → ld."""
        start = time.monotonic()
        cleanup_workdir = False

        if workdir is None:
            workdir = self._create_workdir()
            cleanup_workdir = True
        else:
            workdir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Write source file
            source_path = workdir / "programa.simples"
            source_path.write_text(code, encoding="utf-8")

            # Step 2: simplesc → NASM
            asm_path = workdir / "programa.asm"
            compile_result = self._run_simplesc(source_path, asm_path)
            if not compile_result.success:
                duration_ms = int((time.monotonic() - start) * 1000)
                return CompileResult(
                    success=False,
                    errors=compile_result.errors,
                    error_message=compile_result.error_message,
                    duration_ms=duration_ms,
                )

            # Read generated NASM
            asm_source = asm_path.read_text(encoding="utf-8")

            # Step 3: nasm -f elf32
            obj_path = workdir / "programa.o"
            self._run_nasm(asm_path, obj_path)

            # Step 4: ld -m elf_i386
            binary_path = workdir / "programa"
            self._run_ld(obj_path, binary_path)

            duration_ms = int((time.monotonic() - start) * 1000)
            return CompileResult(
                success=True,
                asm_source=asm_source,
                binary_dir=workdir,
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.warning("compile_timeout: duration_ms=%s", duration_ms)
            return CompileResult(
                success=False,
                error_message=f"Compilation timed out after {config.compile_timeout_s}s",
                duration_ms=duration_ms,
            )
        except FileNotFoundError as e:
            logger.error("compile_tool_missing: tool=%s", str(e))
            duration_ms = int((time.monotonic() - start) * 1000)
            return CompileResult(
                success=False,
                error_message=f"Required tool not found: {e.filename}",
                duration_ms=duration_ms,
            )
        except Exception as e:
            logger.exception("compile_unexpected_error")
            duration_ms = int((time.monotonic() - start) * 1000)
            return CompileResult(
                success=False,
                error_message=f"Unexpected compilation error: {e}",
                duration_ms=duration_ms,
            )

    def _create_workdir(self) -> Path:
        """Create a temporary working directory for compilation."""
        self.tmp_base.mkdir(parents=True, exist_ok=True)
        workdir = self.tmp_base / f"sim-{uuid.uuid4().hex[:12]}"
        workdir.mkdir(parents=True, exist_ok=True)
        return workdir

    def _run_simplesc(self, source: Path, output: Path) -> CompileResult:
        """Run simplesc compiler."""
        try:
            proc = subprocess.run(
                [self.simplesc_path, str(source), "-o", str(output)],
                capture_output=True,
                text=True,
                timeout=config.compile_timeout_s,
            )
        except subprocess.TimeoutExpired:
            raise
        except FileNotFoundError:
            raise

        if proc.returncode != 0:
            errors = parse_compile_errors(proc.stderr)
            if errors:
                return CompileResult(success=False, errors=errors)
            return CompileResult(
                success=False,
                error_message=proc.stderr.strip() or f"simplesc exited with code {proc.returncode}",
            )

        return CompileResult(success=True)

    def _run_nasm(self, asm_path: Path, obj_path: Path) -> None:
        """Run NASM assembler."""
        try:
            subprocess.run(
                [self.nasm_path, "-f", "elf32", str(asm_path), "-o", str(obj_path)],
                capture_output=True,
                text=True,
                timeout=config.compile_timeout_s,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"NASM assembly failed: {e.stderr.strip()}") from e

    def _run_ld(self, obj_path: Path, binary_path: Path) -> None:
        """Run linker (i686-linux-gnu-ld)."""
        try:
            subprocess.run(
                [self.ld_path, "-m", "elf_i386", str(obj_path), "-o", str(binary_path)],
                capture_output=True,
                text=True,
                timeout=config.compile_timeout_s,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Linking failed: {e.stderr.strip()}") from e

    def cleanup(self, workdir: Path) -> None:
        """Remove a compilation working directory."""
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            logger.warning("cleanup_failed: workdir=%s", str(workdir))


# Convenience function for the /api/compile endpoint
def compile_simples(code: str) -> CompileResult:
    """Compile SIMPLES code with fallback to mock when simplesc is not available.

    Uses CompilerService when simplesc is on PATH, otherwise returns
    a mock NASM result for development/demo purposes.
    """
    import shutil
    if shutil.which("simplesc"):
        try:
            service = CompilerService()
            return service.compile(code)
        except Exception:
            logger.warning("Compilação real falhou — usando mock")

    logger.info("simplesc indisponível — usando mock de demonstração")
    return CompileResult(
        success=True,
        asm_source=f"; SIMPLES → NASM (mock — demonstração)\n"
                  f"; Código: {len(code)} bytes\n"
                  f"section .text\n"
                  f"    global _start\n"
                  f"_start:\n"
                  f"    mov eax, 1\n"
                  f"    xor ebx, ebx\n"
                  f"    int 0x80\n",
        duration_ms=0,
    )
