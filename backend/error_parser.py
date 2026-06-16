"""
Parse de erros do compilador/pipeline em formato estruturado.

Módulo compartilhado entre compiler.py e pipeline.py.
"""

from __future__ import annotations


def _parse_errors(stderr: str) -> list[dict]:
    """
    Parseia a saída de erro do simplesc/nasm/ld.

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
