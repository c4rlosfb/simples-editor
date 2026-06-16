"""
Serviço de compilação — pipeline simplesc → NASM.

Invoca o compilador SIMPLES, captura a saída assembly e
parseia erros de compilação em formato estruturado.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

COMPILE_TIMEOUT_S = 15


class CompileError(Exception):
    """Erro de compilação estruturado (linha, coluna, mensagem, fase)."""

    def __init__(self, line: int, column: int, message: str, phase: str = "compiler"):
        self.line = line
        self.column = column
        self.message = message
        self.phase = phase
        super().__init__(f"[{phase}] linha {line}:{column} — {message}")


class CompileResult:
    """Resultado da compilação — NASM em caso de sucesso, ou lista de erros."""

    def __init__(
        self,
        success: bool,
        asm: str = "",
        errors: list[dict] | None = None,
    ):
        self.success = success
        self.asm = asm
        self.errors = errors or []


def compile_simples(code: str) -> CompileResult:
    """
    Compila código SIMPLES e retorna NASM ou erros.

    Fluxo (PRD §7.3):
    1. Escreve o código em arquivo temporário (.simples)
    2. Invoca `simplesc <input> -o <output>`
    3. Se sucesso: lê o .asm gerado e retorna
    4. Se erro: parseia stderr em erros estruturados
    5. Timeout de COMPILE_TIMEOUT_S segundos

    Em desenvolvimento (SIMPLESC_MOCK=true): usa mock quando simplesc não está disponível.
    Em produção (SIMPLESC_MOCK=false, padrão): falha com erro se simplesc não estiver instalado.
    """
    simplesc = shutil.which("simplesc")
    if not simplesc:
        if os.environ.get("SIMPLESC_MOCK", "false").lower() == "true":
            logger.warning("simplesc não encontrado no PATH — usando mock")
            return _mock_compile(code)
        else:
            logger.critical("simplesc não encontrado no PATH — ambiente de produção")
            return CompileResult(
                success=False,
                errors=[{
                    "line": 0,
                    "column": 0,
                    "message": "Compilador simplesc não disponível",
                    "phase": "compiler",
                }],
            )

    with tempfile.TemporaryDirectory(prefix="simples-") as tmp:
        src = Path(tmp) / "programa.simples"
        out = Path(tmp) / "programa.asm"

        src.write_text(code, encoding="utf-8")

        try:
            result = subprocess.run(
                [simplesc, str(src), "-o", str(out)],
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                success=False,
                errors=[{
                    "line": 0,
                    "column": 0,
                    "message": f"Compilação excedeu timeout de {COMPILE_TIMEOUT_S}s",
                    "phase": "compiler",
                }],
            )

        if result.returncode == 0 and out.exists():
            asm = out.read_text(encoding="utf-8")
            logger.info("Compilação OK — %d bytes de NASM gerados", len(asm))
            return CompileResult(success=True, asm=asm)

        errors = _parse_errors(result.stderr)
        logger.warning("Compilação falhou com %d erro(s)", len(errors))
        return CompileResult(success=False, errors=errors)


def _parse_errors(stderr: str) -> list[dict]:
    """
    Parseia a saída de erro do simplesc.

    Formatos esperados:
      "linha:coluna: mensagem"  → lexer/parser
      "linha: mensagem"         → semântico
      "undefined reference"     → linker
    """
    errors: list[dict] = []

    for line in stderr.split("\n"):
        line = line.strip()
        if not line:
            continue

        error: dict = {"line": 0, "column": 0, "message": line, "phase": "compiler"}

        # Tenta extrair linha:coluna
        parts = line.split(":", 2)
        try:
            error["line"] = int(parts[0].strip())
            if len(parts) >= 3:
                col = int(parts[1].strip())
                error["column"] = col
                error["message"] = parts[2].strip()
            elif len(parts) == 2:
                error["message"] = parts[1].strip()
        except (ValueError, IndexError):
            pass  # Mantém os defaults

        # Detecta fase pelo conteúdo da mensagem
        msg_lower = error["message"].lower()
        if any(kw in msg_lower for kw in ("token", "lex", "símbolo", "caracter")):
            error["phase"] = "lexer"
        elif any(kw in msg_lower for kw in ("sintaxe", "esperado", "parser", "gramática")):
            error["phase"] = "parser"
        elif any(kw in msg_lower for kw in ("declarado", "tipo", "semântico", "atribuição")):
            error["phase"] = "semantic"

        errors.append(error)

    return errors


def _mock_compile(code: str) -> CompileResult:
    """
    Compilação mock para dev local sem simplesc.

    Retorna NASM simulado para código que contém 'programa' e 'fim'.
    """
    code_lower = code.lower().strip()

    if not code_lower:
        return CompileResult(
            success=False,
            errors=[{
                "line": 0, "column": 0,
                "message": "Código vazio",
                "phase": "parser",
            }],
        )

    if "programa" not in code_lower:
        return CompileResult(
            success=False,
            errors=[{
                "line": 1, "column": 1,
                "message": "Programa deve começar com 'programa'",
                "phase": "parser",
            }],
        )

    mock_asm = """; NASM x86 gerado por simplesc
; (mock — ambiente sem simplesc instalado)

section .data
    msg db 'Simples!', 10, 0

section .text
    global _start
_start:
    mov eax, 4
    mov ebx, 1
    mov ecx, msg
    mov edx, 10
    int 0x80
    mov eax, 1
    xor ebx, ebx
    int 0x80
"""

    return CompileResult(success=True, asm=mock_asm.strip())
