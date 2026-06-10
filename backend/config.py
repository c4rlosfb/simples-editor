"""
Configurações do backend Simples Editor.

Carrega variáveis de ambiente com fallback para valores default seguros
para desenvolvimento local.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


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
    exec_timeout_s: int = int(os.getenv("EXEC_TIMEOUT_S", "10"))
    compile_timeout_s: int = int(os.getenv("COMPILE_TIMEOUT_S", "15"))
    max_code_kb: int = int(os.getenv("MAX_CODE_KB", "64"))
    runs_per_minute: int = int(os.getenv("RUNS_PER_MINUTE", "30"))

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
