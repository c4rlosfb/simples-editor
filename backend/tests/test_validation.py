"""Tests for input validation module (validation.py)."""

import pytest

from app.validation import validate_code, validate_stdin_data, ValidationError
from app.config import config


class TestValidateCode:
    """Tests for validate_code()."""

    def test_valid_simples_code(self):
        """A standard SIMPLES program should pass validation."""
        code = "programa teste\n  inteiro x\ninicio\n  leia x\n  escreva x\nfim\n"
        validate_code(code)  # Should not raise

    def test_empty_code(self):
        """Empty or whitespace-only code should raise ValidationError."""
        with pytest.raises(ValidationError) as exc:
            validate_code("")
        assert "empty" in str(exc.value.message).lower()

        with pytest.raises(ValidationError):
            validate_code("   \n  \n")

    def test_code_exceeds_max_size(self):
        """Code exceeding max_code_bytes should raise ValidationError."""
        # Temporarily reduce the kb limit for testing
        original_kb = config.max_code_kb
        config.max_code_kb = 1  # ~1KB limit
        try:
            # 2KB should exceed 1KB
            with pytest.raises(ValidationError) as exc:
                validate_code("x" * 2048)
            assert "exceeds" in str(exc.value.message).lower()
        finally:
            config.max_code_kb = original_kb

    def test_code_with_control_characters(self):
        """Code with invalid control characters should raise ValidationError."""
        # NULL byte (0x00) is not allowed
        with pytest.raises(ValidationError):
            validate_code("programa teste\x00\ninicio\nfim")

    def test_code_with_tab_newline_cr(self):
        """Tab, newline, and carriage return should be allowed."""
        validate_code("programa teste\n\tinteiro x\nfim\r\n")  # Should not raise

    def test_code_with_extended_ascii(self):
        """Extended ASCII characters (128-255) should be allowed."""
        validate_code("programa teste\ninicio\nescreva \"café\"\nfim\n")  # 'é' is U+00E9

    def test_boundary_max_size(self):
        """Code at exactly max_code_bytes should pass."""
        original_kb = config.max_code_kb
        # Create code that is exactly 500 bytes
        code = "programa t\ninicio\n" + "x" * 480 + "\nfim\n"
        config.max_code_kb = 1  # 1024 bytes limit
        try:
            validate_code(code)
        finally:
            config.max_code_kb = original_kb


class TestValidateStdin:
    """Tests for validate_stdin_data()."""

    def test_valid_stdin(self):
        """Normal stdin input should pass validation."""
        validate_stdin_data("42\n")

    def test_empty_stdin(self):
        """Empty stdin should pass (it's just an empty string)."""
        validate_stdin_data("")

    def test_stdin_too_large(self):
        """Stdin exceeding max_stdin_bytes should raise ValidationError."""
        original = config.max_stdin_bytes
        config.max_stdin_bytes = 10
        try:
            with pytest.raises(ValidationError):
                validate_stdin_data("a" * 20)
        finally:
            config.max_stdin_bytes = original
