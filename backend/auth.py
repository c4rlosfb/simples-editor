"""
Módulo de autenticação via Supabase.

Gerencia validação de JWT e fornece o decorator @verify_jwt
para proteger endpoints REST e WebSocket.
"""

from __future__ import annotations

import json
import logging
from functools import wraps
from typing import Any, Callable

import jwt as pyjwt
from flask import current_app, g, request

from config import config

logger = logging.getLogger(__name__)

# Cache do JWKS do Supabase — evita fetch em toda request
_jwks_cache: dict[str, Any] | None = None
_jwks_kid: str | None = None


def _get_jwks() -> dict[str, Any]:
    """Obtém as chaves públicas do Supabase para validar o JWT."""
    global _jwks_cache, _jwks_kid

    if _jwks_cache is not None:
        return _jwks_cache

    import urllib.request

    # Suapbase JWKS URL baseada na project URL
    jwks_url = f"{config.supabase_url}/.well-known/jwks.json"
    try:
        with urllib.request.urlopen(jwks_url, timeout=5) as resp:
            jwks: dict = json.loads(resp.read().decode())
    except Exception as exc:
        logger.warning("Falha ao buscar JWKS do Supabase: %s", exc)
        return {}

    # Extrai o primeiro kid (key ID) do cabeçalho
    keys = jwks.get("keys", [])
    if keys:
        _jwks_kid = keys[0].get("kid")
    _jwks_cache = keys[0] if keys else {}

    return _jwks_cache


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Valida um JWT do Supabase.

    Retorna o payload decodificado se válido, None caso contrário.
    """
    if not token:
        return None

    # Remove prefixo 'Bearer ' se presente
    if token.startswith("Bearer "):
        token = token[7:]

    try:
        # Tenta validar com o JWKS primeiro
        jwk_data = _get_jwks()
        if jwk_data:
            public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(
                json.dumps(jwk_data)
            )
            payload = pyjwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        else:
            # Fallback: validação HMAC com o JWT secret
            payload = pyjwt.decode(
                token,
                config.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )

        return payload

    except pyjwt.ExpiredSignatureError:
        logger.warning("JWT expirado")
        return None
    except pyjwt.InvalidTokenError as exc:
        logger.warning("JWT inválido: %s", exc)
        return None


def verify_jwt(f: Callable) -> Callable:
    """
    Decorator para proteger endpoints Flask.

    Extrai o token do header Authorization, valida via Supabase,
    e injeta `g.user_id` e `g.user_email` no contexto da requisição.

    Uso:
        @app.route("/api/protected")
        @verify_jwt
        def protected_route():
            return {"user_id": g.user_id}
    """

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")
        payload = verify_token(auth_header)

        if payload is None:
            return {"error": "Unauthorized", "message": "Token inválido ou expirado"}, 401

        g.user_id = payload.get("sub")
        g.user_email = payload.get("email", "")

        return f(*args, **kwargs)

    return decorated


def verify_websocket_token(token: str) -> dict[str, Any] | None:
    """
    Valida JWT no handshake WebSocket.

    O token pode vir via query param `?token=<jwt>` ou
    header `Sec-WebSocket-Protocol: bearer.<jwt>`.
    """
    return verify_token(token)
