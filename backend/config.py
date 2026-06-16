"""
Configurações do backend Simples Editor.

Carrega variáveis de ambiente com fallback para valores default seguros
para desenvolvimento local.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


def _parse_int_env(name: str, default: int) -> int:
    """Parse an integer environment variable with fallback on error."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "Invalid value for %s=%r — using default %d", name, raw, default
        )
        return default


@dataclass(frozen=True)
class Config:
    # --- Supabase ---
    supabase_url: str = field(
        default_factory=lambda: os.getenv("SUPABASE_URL", "")
    )
    supabase_anon_key: str = field(
        default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", "")
    )
    supabase_jwt_secret: str = field(
        default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", "")
    )

    # --- Limits ---
    exec_timeout_s: int = field(
        default_factory=lambda: _parse_int_env("EXEC_TIMEOUT_S", 10)
    )
    compile_timeout_s: int = field(
        default_factory=lambda: _parse_int_env("COMPILE_TIMEOUT_S", 15)
    )
    max_code_kb: int = field(
        default_factory=lambda: _parse_int_env("MAX_CODE_KB", 64)
    )
    runs_per_minute: int = field(
        default_factory=lambda: _parse_int_env("RUNS_PER_MINUTE", 30)
    )

    # --- Sandbox ---
    sandbox_image: str = os.getenv("SANDBOX_IMAGE", "simples-runner:latest")

    # --- Logging ---
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")

    # --- Paths ---
    tmp_dir: Path = Path(os.getenv("TMP_DIR", "/tmp/simples"))

    # --- Flask ---
    secret_key: str = field(
        default_factory=lambda: os.getenv("FLASK_SECRET_KEY", "dev-only-change-in-prod")
    )


config = Config()
