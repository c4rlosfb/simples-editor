"""Backend configuration (loaded from environment variables)."""

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(key: str, default: str) -> str:
    """Read from environment at call time (not import time)."""
    return os.getenv(key, default)


@dataclass
class Config:
    # Supabase
    supabase_jwt_secret: str = field(
        default_factory=lambda: _env("SUPABASE_JWT_SECRET", "dev-secret-do-not-use-in-prod")
    )
    supabase_url: str = field(
        default_factory=lambda: _env("SUPABASE_URL", "http://localhost:8000")
    )

    # Timeouts
    exec_timeout_s: int = field(default_factory=lambda: int(_env("EXEC_TIMEOUT_S", "10")))
    compile_timeout_s: int = field(default_factory=lambda: int(_env("COMPILE_TIMEOUT_S", "15")))

    # Limits
    max_code_kb: int = field(default_factory=lambda: int(_env("MAX_CODE_KB", "64")))
    runs_per_minute: int = field(default_factory=lambda: int(_env("RUNS_PER_MINUTE", "30")))
    runs_per_minute_ip: int = field(default_factory=lambda: int(_env("RUNS_PER_MINUTE_IP", "120")))
    max_stdin_bytes: int = 4096  # Fixed constant, no env override

    # Sandbox
    sandbox_image: str = field(
        default_factory=lambda: _env("SANDBOX_IMAGE", "simples-runner:latest")
    )

    # Logging
    log_level: str = field(default_factory=lambda: _env("LOG_LEVEL", "INFO"))

    # Paths
    tmp_base: Path = field(default_factory=lambda: Path(_env("TMP_BASE", "/tmp/simples")))

    # Version
    version: str = "1.0.0"

    @property
    def max_code_bytes(self) -> int:
        return self.max_code_kb * 1024


config = Config()
