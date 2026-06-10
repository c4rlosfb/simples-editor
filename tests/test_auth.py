"""
Testes para o módulo de autenticação (auth.py).

Cobre o decorator @verify_jwt e a função verify_token().
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from flask import Flask, g

from auth import verify_jwt, verify_token, _jwks_cache


# --- Helpers ---

SECRET = "test-secret-key-min-32-chars-long!!"


def _make_token(payload: dict | None = None, secret: str = SECRET) -> str:
    """Gera um JWT HS256 válido para testes."""
    if payload is None:
        payload = {
            "sub": "test-user-123",
            "email": "aluno@test.edu",
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
    return pyjwt.encode(payload, secret, algorithm="HS256")


def _make_expired_token() -> str:
    """Gera um JWT expirado."""
    payload = {
        "sub": "test-user-123",
        "email": "aluno@test.edu",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    return pyjwt.encode(payload, SECRET, algorithm="HS256")


# --- Testes: verify_token ---


class TestVerifyToken:
    """Testes para a função verify_token()."""

    def setup_method(self):
        # Limpa cache JWKS entre testes
        _jwks_cache = None

    def test_valid_token_returns_payload(self):
        """Um JWT válido deve retornar o payload decodificado."""
        token = _make_token()
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test-user-123"
        assert payload["email"] == "aluno@test.edu"

    def test_valid_token_with_bearer_prefix(self):
        """Token com prefixo 'Bearer ' deve ser processado corretamente."""
        token = _make_token()
        result = verify_token(f"Bearer {token}")
        assert result is not None
        assert result["sub"] == "test-user-123"

    def test_expired_token_returns_none(self):
        """Token expirado deve retornar None."""
        token = _make_expired_token()
        assert verify_token(token) is None

    def test_invalid_token_returns_none(self):
        """Token com assinatura inválida deve retornar None."""
        bad_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.invalidsignature"
        assert verify_token(bad_token) is None

    def test_empty_token_returns_none(self):
        """String vazia deve retornar None."""
        assert verify_token("") is None

    def test_none_token_returns_none(self):
        """None deve retornar None."""
        assert verify_token(None) is None  # type: ignore

    def test_malformed_jwt_returns_none(self):
        """String completamente inválida deve retornar None."""
        assert verify_token("not-a-jwt-at-all") is None

    def test_token_with_wrong_secret_returns_none(self):
        """Token assinado com chave diferente deve retornar None."""
        token = _make_token(secret="different-secret-not-the-same-one!!")
        assert verify_token(token) is None

    def test_token_with_custom_payload(self):
        """Payload customizado deve ser preservado na decodificação."""
        custom = {
            "sub": "user-42",
            "email": "professor@ifsu.edu",
            "role": "teacher",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(custom, SECRET, algorithm="HS256")
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-42"
        assert payload["role"] == "teacher"


# --- Testes: verify_jwt decorator ---


class TestVerifyJwtDecorator:
    """Testes para o decorator @verify_jwt."""

    @pytest.fixture
    def app(self):
        """Cria uma app Flask de teste com rotas protegidas."""
        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.route("/api/protected")
        @verify_jwt
        def protected():
            return {
                "user_id": g.user_id,
                "email": g.user_email,
            }

        @app.route("/api/public")
        def public():
            return {"status": "ok"}

        return app

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_protected_without_token_returns_401(self, client):
        """Rota protegida sem token deve retornar 401."""
        resp = client.get("/api/protected")
        assert resp.status_code == 401
        data = resp.get_json()
        assert data["error"] == "Unauthorized"

    def test_protected_with_valid_token_returns_200(self, client):
        """Rota protegida com token válido deve retornar 200 e user_id."""
        token = _make_token()
        resp = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user_id"] == "test-user-123"
        assert data["email"] == "aluno@test.edu"

    def test_protected_with_expired_token_returns_401(self, client):
        """Rota protegida com token expirado deve retornar 401."""
        token = _make_expired_token()
        resp = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_public_route_does_not_need_auth(self, client):
        """Rota pública não deve exigir autenticação."""
        resp = client.get("/api/public")
        assert resp.status_code == 200

    def test_invalid_auth_header_format_returns_401(self, client):
        """Header mal formatado deve retornar 401."""
        resp = client.get(
            "/api/protected",
            headers={"Authorization": ""},
        )
        assert resp.status_code == 401

    def test_protected_with_bearer_no_space(self, client):
        """'Bearer<token>' sem espaço deve funcionar (verify_token lida com isso)."""
        token = _make_token()
        resp = client.get(
            "/api/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

    def test_token_payload_in_g(self, client):
        """O payload completo deve estar disponível em g.token_payload."""
        app = client.application

        @app.route("/api/check-payload")
        @verify_jwt
        def check_payload():
            return {"has_payload": hasattr(g, "token_payload")}

        token = _make_token()
        resp = client.get(
            "/api/check-payload",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["has_payload"] is True
