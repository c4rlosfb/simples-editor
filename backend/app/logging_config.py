"""Structured logging configuration.

Configures structlog for JSON-structured logging as described in PRD §16.1.
"""

import logging
import structlog


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging.

    Args:
        level: Log level string (e.g., "INFO", "DEBUG").
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer()  # Pretty in dev; swap to JSON in prod
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
        force=True,
    )
