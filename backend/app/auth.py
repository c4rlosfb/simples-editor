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
    """Validate a JWT and return its payload.

    Tries the configured Supabase JWT secret first, then falls back to
    the development secret for demo mode compatibility.

    Args:
        token: The raw JWT string (Bearer <token>).

    Returns:
        Decoded JWT payload containing at least 'sub' (user_id).

    Raises:
        AuthError: If the token is invalid, expired, or malformed.
    """
    secrets_to_try = [config.supabase_jwt_secret]
    dev_secret = "dev-secret-do-not-use-in-prod"
    if config.supabase_jwt_secret != dev_secret:
        secrets_to_try.append(dev_secret)

    last_error = None
    for secret in secrets_to_try:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"require": ["sub", "exp"]},
            )
            return payload
        except jwt.InvalidTokenError as e:
            last_error = e

    if isinstance(last_error, jwt.ExpiredSignatureError):
        raise AuthError("Token has expired", 401)
    raise AuthError(f"Invalid token: {last_error}", 401)


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
