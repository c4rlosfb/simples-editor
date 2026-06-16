"""Input validation utilities.

Validates code and stdin input against the constraints defined in
PRD §11.5.
"""

from app.config import config


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def validate_code(code: str) -> None:
    """Validate SIMPLES source code against size and character constraints.

    Args:
        code: The source code to validate.

    Raises:
        ValidationError: If any constraint is violated.
    """
    if not code or not code.strip():
        raise ValidationError("Code must not be empty")

    code_bytes = len(code.encode("utf-8"))
    if code_bytes > config.max_code_bytes:
        raise ValidationError(
            f"Code exceeds maximum size of {config.max_code_kb} KB "
            f"(got {code_bytes // 1024} KB)"
        )

    # Only allow tab, newline, carriage return, and printable ASCII/extended
    for i, char in enumerate(code):
        code_point = ord(char)
        # Allow: tab(9), newline(10), carriage return(13),
        # printable ASCII (32-126), extended ASCII (128-255)
        if not (
            char in "\t\n\r"
            or 32 <= code_point <= 126
            or 128 <= code_point <= 255
        ):
            raise ValidationError(
                f"Code contains invalid character at position {i}: "
                f"U+{code_point:04X}"
            )


def validate_stdin_data(data: str) -> None:
    """Validate stdin data from WebSocket messages.

    Args:
        data: The stdin data string.

    Raises:
        ValidationError: If the data exceeds size limits.
    """
    data_bytes = len(data.encode("utf-8"))
    if data_bytes > config.max_stdin_bytes:
        raise ValidationError(
            f"Stdin data exceeds maximum of {config.max_stdin_bytes // 1024} KB "
            f"(got {data_bytes} bytes)"
        )
