import os
import subprocess
import tempfile
import shutil
import logging
from typing import Optional

from .pty_strategy import PtyExecutionStrategy

logger = logging.getLogger(__name__)

SIMPLESC = shutil.which('simplesc') or '/usr/local/bin/simplesc'
NASM = shutil.which('nasm') or '/usr/bin/nasm'
LD_I386 = shutil.which('i686-linux-gnu-ld') or '/usr/bin/i686-linux-gnu-ld'
COMPILE_TIMEOUT = 15


class CompilerService:
    """
    Facade that orchestrates the full pipeline:
        simplesc -> nasm -> ld -> sandbox execution
    """

    def __init__(self, pty_strategy: Optional[PtyExecutionStrategy] = None):
        self.pty_strategy = pty_strategy or PtyExecutionStrategy()

    def compile(self, code: str) -> dict:
        """
        Compile SIMPLES source through the full pipeline.
        Returns {"success": True, "asm": "...", "binary_dir": "..."}
        or {"success": False, "errors": [...]}.

        Note: on success, the caller is responsible for cleaning up
        binary_dir after execution completes.
        """
        tmpdir = tempfile.mkdtemp(prefix='simples_')
        try:
            source_path = os.path.join(tmpdir, 'programa.simples')
            asm_path = os.path.join(tmpdir, 'programa.asm')
            obj_path = os.path.join(tmpdir, 'programa.o')
            bin_path = os.path.join(tmpdir, 'programa')

            # Write source
            with open(source_path, 'w', encoding='utf-8') as f:
                f.write(code)

            # Step 1: simplesc -> NASM
            try:
                result = subprocess.run(
                    [SIMPLESC, source_path, '-o', asm_path],
                    capture_output=True, text=True,
                    timeout=COMPILE_TIMEOUT
                )
            except subprocess.TimeoutExpired:
                return {"success": False, "errors": [
                    {"line": 0, "column": 0, "message": "Tempo de compilacao excedido (15s)", "phase": "compiler"}
                ]}
            except FileNotFoundError:
                return {"success": False, "errors": [
                    {"line": 0, "column": 0, "message": "simplesc nao encontrado no servidor", "phase": "system"}
                ]}

            if result.returncode != 0:
                errors = self._parse_errors(result.stderr)
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"success": False, "errors": errors}

            # Read NASM
            with open(asm_path, 'r', encoding='utf-8') as f:
                asm_content = f.read()

            # Step 2: nasm -> object file
            try:
                subprocess.run(
                    [NASM, '-f', 'elf32', asm_path, '-o', obj_path],
                    capture_output=True, text=True,
                    timeout=COMPILE_TIMEOUT, check=True
                )
            except subprocess.CalledProcessError as e:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"success": False, "errors": [
                    {"line": 0, "column": 0, "message": f"NASM error: {e.stderr.strip()}", "phase": "assembler"}
                ]}
            except FileNotFoundError:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"success": False, "errors": [
                    {"line": 0, "column": 0, "message": "nasm nao encontrado no servidor", "phase": "system"}
                ]}

            # Step 3: ld -> executable
            try:
                subprocess.run(
                    [LD_I386, obj_path, '-o', bin_path],
                    capture_output=True, text=True,
                    timeout=COMPILE_TIMEOUT, check=True
                )
            except subprocess.CalledProcessError as e:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"success": False, "errors": [
                    {"line": 0, "column": 0, "message": f"Linker error: {e.stderr.strip()}", "phase": "linker"}
                ]}
            except FileNotFoundError:
                shutil.rmtree(tmpdir, ignore_errors=True)
                return {"success": False, "errors": [
                    {"line": 0, "column": 0, "message": "Linker i686 nao encontrado no servidor", "phase": "system"}
                ]}

            # Success - binary_dir must outlive this call for execution
            return {"success": True, "asm": asm_content, "binary_dir": tmpdir}

        except Exception as e:
            shutil.rmtree(tmpdir, ignore_errors=True)
            logger.exception("Compilation failed")
            return {"success": False, "errors": [
                {"line": 0, "column": 0, "message": f"Erro: {str(e)}", "phase": "system"}
            ]}

    def cleanup_binary_dir(self, binary_dir: str):
        """Safely remove a temporary binary directory after execution."""
        if binary_dir and os.path.exists(binary_dir):
            shutil.rmtree(binary_dir, ignore_errors=True)
            logger.debug(f"Cleaned up {binary_dir}")

    async def compile_and_run(self, code: str):
        """
        Full pipeline: compile -> execute -> yield events.
        Ensures cleanup of temp directory after execution.
        """
        yield {"type": "compile_started"}

        compile_result = self.compile(code)
        if not compile_result.get("success"):
            yield {"type": "compile_error", "errors": compile_result.get("errors", [])}
            return

        yield {"type": "asm_generated", "asm": compile_result["asm"]}
        yield {"type": "exec_started"}

        binary_dir = compile_result.get("binary_dir")
        try:
            if binary_dir and os.path.exists(os.path.join(binary_dir, "programa")):
                async for event in self.pty_strategy.execute(binary_dir):
                    yield event
            else:
                yield {"type": "error", "message": "Binary not found after compilation"}
        finally:
            if binary_dir:
                self.cleanup_binary_dir(binary_dir)

    def _parse_errors(self, stderr: str) -> list:
        """Parse simplesc compiler errors."""
        errors = []
        for line in stderr.split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split(':', 2)
            try:
                line_num = int(parts[0].strip())
                if len(parts) >= 3:
                    col = int(parts[1].strip())
                    msg = parts[2].strip()
                else:
                    col = 1
                    msg = parts[1].strip() if len(parts) > 1 else line
                errors.append({"line": line_num, "column": col, "message": msg, "phase": "compiler"})
            except (ValueError, IndexError):
                errors.append({"line": 0, "column": 0, "message": line, "phase": "compiler"})
        return errors if errors else [{"line": 0, "column": 0, "message": stderr.strip(), "phase": "compiler"}]
