"""JWT verification decorator and utilities.

Validates Supabase JWTs using the project's JWT secret.
Implements the pattern described in PRD §9 & §11.1.
"""

import functools
import hashlib
from typing import Callable

import jwt
from flask import request, jsonify, g

from app.config import config


class AuthError(Exception):
    """Raised when authentication/authorization fails."""

    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def verify_jwt(token: str) -> dict:
    """Validate a Supabase JWT and return its payload.

    Args:
        token: The raw JWT string (Bearer <token>).

    Returns:
        Decoded JWT payload containing at least 'sub' (user_id).

    Raises:
        AuthError: If the token is invalid, expired, or malformed.
    """
    try:
        payload = jwt.decode(
            token,
            config.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"require": ["sub", "exp"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired", 401)
    except jwt.InvalidTokenError as e:
        raise AuthError(f"Invalid token: {e}", 401)


def extract_user_id(payload: dict) -> str:
    """Extract a consistent user identifier from JWT payload.

    Uses the 'sub' claim, hashed for privacy in logs.
    """
    return payload["sub"]


def hash_user_id(user_id: str) -> str:
    """Return a SHA-256 hash of the user_id for privacy-safe logging."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def require_auth(f: Callable) -> Callable:
    """Decorator that validates JWT from Authorization header.

    On success, sets g.user_id and g.jwt_payload.
    On failure, returns a 401 JSON response.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header[len("Bearer "):]
        try:
            payload = verify_jwt(token)
            g.user_id = extract_user_id(payload)
            g.jwt_payload = payload
        except AuthError as e:
            return jsonify({"error": e.message}), e.status_code

        return f(*args, **kwargs)

    return decorated
