"""Tests for logging configuration (logging_config.py)."""

from unittest.mock import patch


class TestSetupLogging:
    """Tests for setup_logging()."""

    def test_setup_logging_default_level(self):
        """setup_logging should configure structlog with default INFO level."""
        from app.logging_config import setup_logging
        # Should not raise
        setup_logging()

    def test_setup_logging_custom_level(self):
        """setup_logging should accept custom log level."""
        from app.logging_config import setup_logging
        setup_logging("DEBUG")
        setup_logging("WARNING")

    def test_setup_logging_invalid_level(self):
        """setup_logging should fallback to INFO for invalid level."""
        from app.logging_config import setup_logging
        # Should not raise - falls back to INFO
        setup_logging("INVALID_LEVEL")
