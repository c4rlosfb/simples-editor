"""
Serviço de linking — invoca i686-linux-gnu-ld para gerar binários ELF i386.

Portável entre hosts x86_64 e ARM64 via binutils cross-target.
Referência: PRD §8.3 e §14.3
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Linker cross-target — funciona em qualquer arquitetura de host
LD = "i686-linux-gnu-ld"


def link_object(
    object_path: Path,
    output_path: Path,
    *,
    timeout_s: int = 15,
) -> tuple[bool, str]:
    """
    Linka um arquivo .o (ELF32) em um executável ELF i386.

    Args:
        object_path: Caminho para o arquivo .o gerado pelo NASM.
        output_path: Caminho de saída para o executável.
        timeout_s: Timeout em segundos.

    Returns:
        Tuple (sucesso, mensagem): (True, "") em caso de sucesso,
        (False, stderr) em caso de erro.
    """
    if not object_path.exists():
        return False, f"Arquivo objeto não encontrado: {object_path}"

    cmd = [
        LD,
        "-m", "elf_i386",       # Target: ELF 32-bit i386
        "-o", str(output_path),
        str(object_path),
    ]

    logger.debug("Linkando: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        if result.returncode == 0 and output_path.exists():
            logger.info(
                "Link concluído: %s → %s (%d bytes)",
                object_path.name,
                output_path.name,
                output_path.stat().st_size,
            )
            return True, ""

        stderr = result.stderr.strip()
        logger.warning("Link falhou (exit %d): %s", result.returncode, stderr)
        return False, stderr or "Erro desconhecido no linker"

    except subprocess.TimeoutExpired:
        logger.error("Link timeout após %ds", timeout_s)
        return False, f"Link excedeu timeout de {timeout_s}s"

    except FileNotFoundError:
        logger.critical(
            "%s não encontrado. Instale binutils-i686-linux-gnu.", LD
        )
        return False, f"Linker '{LD}' não encontrado no PATH"


def verify_toolchain() -> dict[str, bool]:
    """
    Verifica se as ferramentas do toolchain estão disponíveis.

    Útil para health check e diagnóstico.
    """
    tools = {
        "nasm": "nasm",
        "ld_i686": LD,
    }

    result = {}
    for name, binary in tools.items():
        found = subprocess.run(
            ["which", binary],
            capture_output=True,
            text=True,
        ).returncode == 0
        result[name] = found
        if not found:
            logger.warning("Ferramenta '%s' (%s) não encontrada", name, binary)

    return result
