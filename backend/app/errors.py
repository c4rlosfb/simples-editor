"""Compile error parsing utilities.

Parses output from simplesc (lexer/parser/semantic phases) into
structured {line, column, message, phase} objects as described in
PRD §9.2.2 and the machine state diagram §9.2.3.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class CompileError:
    """A structured compile error with position info."""

    phase: str  # "lexer" | "parser" | "semantic"
    line: int
    column: int
    message: str


# Example simplesc error formats (adjust to match actual simplesc output):
#   "line 4, col 7: erro lexico: caractere invalido '@'"
#   "line 12, col 1: erro sintatico: esperado 'fim', encontrado 'inicio'"
#   "line 8, col 5: erro semantico: variavel 'x' nao declarada"
_ERROR_PATTERNS = [
    # Lexer errors
    re.compile(
        r"line\s+(?P<line>\d+)\s*,\s*col\s+(?P<col>\d+)\s*:\s*erro\s+lexico\s*:\s*(?P<msg>.+)",
        re.IGNORECASE,
    ),
    # Parser errors
    re.compile(
        r"line\s+(?P<line>\d+)\s*,\s*col\s+(?P<col>\d+)\s*:\s*erro\s+sintatico\s*:\s*(?P<msg>.+)",
        re.IGNORECASE,
    ),
    # Semantic errors
    re.compile(
        r"line\s+(?P<line>\d+)\s*,\s*col\s+(?P<col>\d+)\s*:\s*erro\s+semantico\s*:\s*(?P<msg>.+)",
        re.IGNORECASE,
    ),
    # Generic "line X, col Y: error/message" fallback
    re.compile(
        r"line\s+(?P<line>\d+)\s*,\s*col\s+(?P<col>\d+)\s*:\s*(?P<msg>.+)",
        re.IGNORECASE,
    ),
]

_PHASE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"erro\s+lexico", re.IGNORECASE), "lexer"),
    (re.compile(r"erro\s+sintatico", re.IGNORECASE), "parser"),
    (re.compile(r"erro\s+semantico", re.IGNORECASE), "semantic"),
]


def _infer_phase(line_text: str) -> str:
    """Infer the compilation phase from error text."""
    for pattern, phase in _PHASE_PATTERNS:
        if pattern.search(line_text):
            return phase
    return "unknown"


def parse_compile_errors(stderr: str) -> list[CompileError]:
    """Parse simplesc stderr into structured error objects.

    Args:
        stderr: Raw stderr output from simplesc.

    Returns:
        List of CompileError objects. Empty list if no errors matched.
    """
    errors: list[CompileError] = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        for pattern in _ERROR_PATTERNS:
            match = pattern.search(line)
            if match:
                phase = _infer_phase(line)
                errors.append(
                    CompileError(
                        phase=phase,
                        line=int(match.group("line")),
                        column=int(match.group("col")),
                        message=match.group("msg").strip(),
                    )
                )
                break  # first matching pattern wins
    return errors
