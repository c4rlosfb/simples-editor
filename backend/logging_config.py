"""
Configuração de logging estruturado com structlog.

Formato JSON consistente para todos os logs do backend.
Referência: PRD §16.1
"""

from __future__ import annotations

import logging
import os
import uuid

import structlog
from flask import Flask, g, has_request_context, request

# Campos fixos do log JSON (PRD §16.1):
#   timestamp, level, logger, event, user_id, duration_ms, exit_code, request_id


def configure_logging(app: Flask | None = None, log_level: str = "INFO") -> None:
    """
    Configura structlog como logger padrão da aplicação.

    Formato: JSON em produção, console colorido em desenvolvimento.

    Args:
        app: Instância Flask para configurar o logger da aplicação.
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR).
    """
    log_format = os.getenv("LOG_FORMAT", "json")

    # Processadores comuns (executados em ordem)
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "json":
        # Produção: JSON puro
        structlog.configure(
            processors=shared_processors + [
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Desenvolvimento: console colorido
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

    # Configura o logger raiz
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    if app:
        app.logger = structlog.get_logger("simples.app")


def get_logger(name: str = "simples") -> structlog.stdlib.BoundLogger:
    """
    Obtém um logger estruturado com o nome especificado.

    Exemplo:
        logger = get_logger("simples.compiler")
        logger.info("compilacao_ok", user_id="abc", duration_ms=234)
    """
    return structlog.get_logger(name)


def bind_request_context() -> None:
    """
    Vincula request_id e user_id ao contexto structlog.

    Deve ser chamado no before_request do Flask para que
    todos os logs da requisição tenham esses campos.
    """
    request_id = str(uuid.uuid4())[:8]
    structlog.contextvars.bind_contextvars(request_id=request_id)

    if has_request_context():
        g.request_id = request_id

        # user_id disponível se a rota usar @verify_jwt
        user_id = getattr(g, "user_id", None)
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=user_id)


def clear_request_context(*args, **kwargs) -> None:
    """Limpa o contexto structlog ao final da requisição."""
    structlog.contextvars.clear_contextvars()
