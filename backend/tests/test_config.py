"""Tests for configuration module (config.py)."""

import os
from pathlib import Path

from app.config import Config, config


class TestConfigDefaults:
    """Tests for default configuration values."""

    def test_default_values(self):
        """Default config should have sensible values."""
        cfg = Config()
        assert cfg.exec_timeout_s == 10
        assert cfg.compile_timeout_s == 15
        assert cfg.max_code_kb == 64
        assert cfg.max_code_bytes == 64 * 1024
        assert cfg.runs_per_minute == 30
        assert cfg.runs_per_minute_ip == 120
        assert cfg.max_stdin_bytes == 4096
        assert cfg.version == "1.0.0"
        assert cfg.log_level == "INFO"

    def test_env_override(self):
        """Environment variables should override defaults when creating a fresh Config."""
        old_exec = os.environ.get("EXEC_TIMEOUT_S")
        old_compile = os.environ.get("COMPILE_TIMEOUT_S")
        old_max = os.environ.get("MAX_CODE_KB")
        try:
            os.environ["EXEC_TIMEOUT_S"] = "30"
            os.environ["COMPILE_TIMEOUT_S"] = "45"
            os.environ["MAX_CODE_KB"] = "128"

            cfg = Config()
            assert cfg.exec_timeout_s == 30
            assert cfg.compile_timeout_s == 45
            assert cfg.max_code_kb == 128
            assert cfg.max_code_bytes == 128 * 1024
        finally:
            if old_exec:
                os.environ["EXEC_TIMEOUT_S"] = old_exec
            else:
                del os.environ["EXEC_TIMEOUT_S"]
            if old_compile:
                os.environ["COMPILE_TIMEOUT_S"] = old_compile
            else:
                del os.environ["COMPILE_TIMEOUT_S"]
            if old_max:
                os.environ["MAX_CODE_KB"] = old_max
            else:
                del os.environ["MAX_CODE_KB"]

    def test_tmp_base(self):
        """tmp_base should be a Path."""
        assert isinstance(config.tmp_base, Path)

    def test_sandbox_image_default(self):
        """Sandbox image should default to simples-runner:latest."""
        assert "simples-runner" in config.sandbox_image

    def test_supabase_jwt_secret_default(self):
        """JWT secret should have a development default."""
        assert config.supabase_jwt_secret is not None
