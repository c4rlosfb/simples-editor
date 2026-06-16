"""
Testes para o endpoint /api/health (Issue #12).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from flask import Flask

from routes.health import bp as health_bp


@pytest.fixture
def app() -> Flask:
    """Fixture — app Flask com o blueprint de health."""
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    return app


@pytest.fixture
def client(app: Flask):
    """Fixture — test client."""
    return app.test_client()


class TestHealthEndpoint:
    """Testes para GET /api/health."""

    def test_health_returns_200(self, client):
        """Endpoint deve retornar HTTP 200."""
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        """Resposta deve ser JSON com os campos obrigatórios."""
        resp = client.get("/api/health")
        data = resp.get_json()

        assert data is not None
        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert "timestamp" in data

    def test_health_components_structure(self, client):
        """Components deve conter flask, simplesc e docker."""
        resp = client.get("/api/health")
        data = resp.get_json()

        components = data["components"]
        assert "flask" in components
        assert "simplesc" in components
        assert "docker" in components

    def test_health_flask_is_ok(self, client):
        """Flask deve estar sempre 'ok'."""
        resp = client.get("/api/health")
        data = resp.get_json()
        assert data["components"]["flask"] == "ok"

    def test_health_status_field(self, client):
        """Status deve ser 'ok' ou 'degraded'."""
        resp = client.get("/api/health")
        data = resp.get_json()
        assert data["status"] in ("ok", "degraded")

    def test_health_version_is_string(self, client):
        """Version deve ser uma string não vazia."""
        resp = client.get("/api/health")
        data = resp.get_json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

    def test_health_timestamp_is_isoformat(self, client):
        """Timestamp deve estar em formato ISO 8601."""
        resp = client.get("/api/health")
        data = resp.get_json()
        assert "T" in data["timestamp"]
        assert data["timestamp"].endswith("Z") or "+" in data["timestamp"]

    def test_health_content_type(self, client):
        """Content-Type deve ser application/json."""
        resp = client.get("/api/health")
        assert resp.content_type == "application/json"
