"""
Health check endpoint.

GET /api/health → JSON com status da aplicação e componentes.
"""

from __future__ import annotations

import logging
import os
import shutil
import socket
from datetime import datetime, timezone

from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.route("/health", methods=["GET"])
def health():
    """
    Retorna o status atual da aplicação.

    Response (200):
    ```json
    {
      "status": "ok",
      "version": "0.1.0",
      "components": {
        "flask": "ok",
        "simplesc": "ok" | "error",
        "docker": "ok" | "error"
      },
      "timestamp": "2025-01-01T00:00:00Z"
    }
    ```
    """
    components: dict[str, str] = {}
    all_ok = True

    # 1. Flask — sempre ok se estamos aqui
    components["flask"] = "ok"

    # 2. simplesc — verifica binário no PATH
    if _check_simplesc():
        components["simplesc"] = "ok"
    else:
        components["simplesc"] = "error"
        all_ok = False

    # 3. Docker — verifica socket do daemon
    if _check_docker_socket():
        components["docker"] = "ok"
    else:
        components["docker"] = "error"
        all_ok = False

    payload = {
        "status": "ok" if all_ok else "degraded",
        "version": _get_version(),
        "components": components,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return jsonify(payload), 200


def _check_simplesc() -> bool:
    """Verifica se o binário `simplesc` está disponível no PATH."""
    try:
        return shutil.which("simplesc") is not None
    except Exception as exc:
        logger.warning("Erro ao verificar simplesc: %s", exc)
        return False


def _check_docker_socket() -> bool:
    """Verifica se o socket do Docker daemon está acessível."""
    sock_paths = ["/var/run/docker.sock"]

    # Suporte a Docker Desktop no WSL / Linux
    if "DOCKER_HOST" in os.environ:
        sock_paths.insert(0, os.environ["DOCKER_HOST"])

    for path in sock_paths:
        if path.startswith("unix://"):
            path = path.removeprefix("unix://")
        try:
            if os.path.exists(path):
                # Testa se o socket responde
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect(path)
                sock.close()
                return True
        except (FileNotFoundError, ConnectionRefusedError, OSError, socket.timeout) as exc:
            logger.debug("Socket Docker não disponível em %s: %s", path, exc)
            continue

    return False


def _get_version() -> str:
    """Retorna a versão atual da aplicação."""
    # TODO: ler de pyproject.toml ou __version__ quando disponível
    return "0.1.0"
