"""REST API routes.

Implements the REST endpoints defined in PRD §9.1:
- GET /api/health
- POST /api/auth/verify
- GET /api/limits
"""

import logging
import subprocess

from flask import Blueprint, jsonify, g, request

from app.auth import require_auth, verify_jwt, extract_user_id
from app.config import config

logger = logging.getLogger("simples.routes")
routes_bp = Blueprint("routes", __name__)


@routes_bp.route("/api/health")
def health():
    """Public health check endpoint.

    Returns status of all components: compiler, docker, and supabase auth.
    """
    # Check compiler availability
    compiler_status = {"status": "unknown"}
    try:
        result = subprocess.run(
            ["simplesc", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = result.stdout.strip() or result.stderr.strip() or "unknown"
        compiler_status = {"status": "ok", "version": version}
    except FileNotFoundError:
        compiler_status = {"status": "unavailable", "version": "not found"}
    except subprocess.TimeoutExpired:
        compiler_status = {"status": "timeout"}

    # Check NASM availability
    nasm_status = {"status": "unknown"}
    try:
        result = subprocess.run(
            ["nasm", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = result.stdout.strip() or "unknown"
        nasm_status = {"status": "ok", "version": version}
    except FileNotFoundError:
        nasm_status = {"status": "unavailable", "version": "not found"}

    # Check Docker availability
    docker_status = {"status": "unknown"}
    try:
        import docker
        client = docker.from_env()
        client.ping()
        docker_status = {"status": "ok"}
    except Exception:
        docker_status = {"status": "unavailable"}

    # Check Supabase config
    supabase_status = {"status": "ok"}
    if not config.supabase_jwt_secret or config.supabase_jwt_secret == "dev-secret-do-not-use-in-prod":
        supabase_status = {"status": "degraded", "message": "Using development JWT secret"}

    components = {
        "compiler": compiler_status,
        "nasm": nasm_status,
        "docker": docker_status,
        "supabase": supabase_status,
    }

    overall_status = "healthy"
    for key, comp in components.items():
        if comp.get("status") in ("unavailable", "timeout"):
            overall_status = "degraded"
            break

    return jsonify({
        "status": overall_status,
        "version": config.version,
        "components": components,
    })


@routes_bp.route("/api/auth/verify", methods=["POST"])
@require_auth
def auth_verify():
    """Validate JWT and return user info.

    Requires Authorization: Bearer <jwt> header.
    """
    return jsonify({
        "valid": True,
        "user_id": g.user_id,
        "email": g.jwt_payload.get("email", ""),
    })


@routes_bp.route("/api/limits")
def limits():
    """Return current system limits."""
    return jsonify({
        "exec_timeout_s": config.exec_timeout_s,
        "compile_timeout_s": config.compile_timeout_s,
        "max_code_kb": config.max_code_kb,
        "runs_per_minute": config.runs_per_minute,
    })
