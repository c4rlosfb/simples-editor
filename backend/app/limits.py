"""Rate limiting configuration.

Implements the rate limiting rules defined in PRD §11.4:
- 30 executions/minute per user_id
- 120 executions/minute per IP

Uses Flask-Limiter with in-memory backend (Redis in production).
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import config


def _get_user_id():
    """Try to get user_id from flask.g (set by require_auth)."""
    from flask import g
    try:
        return g.user_id
    except (AttributeError, RuntimeError):
        return None


def _key_func_user():
    """Rate limit key function: user_id if authenticated, else IP."""
    uid = _get_user_id()
    if uid:
        return f"user:{uid}"
    return f"ip:{get_remote_address()}"


limiter = Limiter(
    key_func=_key_func_user,
    default_limits=[f"{config.runs_per_minute}/minute"],
    storage_uri="memory://",
)

# Per-IP rate limit (separate from user-level)
ip_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{config.runs_per_minute_ip}/minute"],
    storage_uri="memory://",
)
