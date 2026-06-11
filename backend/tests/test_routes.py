"""Tests for REST routes (routes.py)."""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.config import config
from tests.conftest import create_test_jwt


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_health_returns_json(self, app):
        """Health endpoint should return JSON with status."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(*args, **kwargs):
                m = MagicMock()
                m.returncode = 0
                m.stdout = "simplesc 1.0"
                m.stderr = ""
                return m
            mock_run.side_effect = mock_subprocess

            with patch("docker.from_env") as mock_docker:
                mock_client = MagicMock()
                mock_docker.return_value = mock_client

                with app.test_client() as client:
                    response = client.get("/api/health")
                    data = json.loads(response.data)

                    assert response.status_code == 200
                    assert data["status"] == "healthy"
                    assert data["version"] == config.version
                    assert "components" in data

    def test_health_compiler_unavailable(self, app):
        """Health should report degraded when compiler is missing."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with patch("docker.from_env") as mock_docker:
                mock_client = MagicMock()
                mock_docker.return_value = mock_client

                with app.test_client() as client:
                    response = client.get("/api/health")
                    data = json.loads(response.data)
                    assert data["components"]["compiler"]["status"] == "unavailable"

    def test_health_docker_unavailable(self, app):
        """Health should report degraded when Docker is unavailable."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(*args, **kwargs):
                m = MagicMock()
                m.returncode = 0
                m.stdout = "simplesc 1.0"
                m.stderr = ""
                return m
            mock_run.side_effect = mock_subprocess

            with patch("docker.from_env") as mock_docker:
                mock_docker.side_effect = Exception("Docker not available")

                with app.test_client() as client:
                    response = client.get("/api/health")
                    data = json.loads(response.data)
                    assert data["components"]["docker"]["status"] == "unavailable"
                    assert data["status"] == "degraded"


class TestAuthVerifyEndpoint:
    """Tests for POST /api/auth/verify."""

    def test_valid_token(self, app, client, auth_header):
        """Valid JWT should return user info."""
        response = client.post("/api/auth/verify", headers=auth_header)
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["valid"] is True
        assert "user_id" in data

    def test_missing_token(self, client):
        """Missing token should return 401."""
        response = client.post("/api/auth/verify")
        assert response.status_code == 401

    def test_invalid_token(self, client):
        """Invalid token should return 401."""
        response = client.post(
            "/api/auth/verify",
            headers={"Authorization": "Bearer invalidtoken"},
        )
        assert response.status_code == 401


class TestLimitsEndpoint:
    """Tests for GET /api/limits."""

    def test_limits_returns_config_values(self, client):
        """Limits endpoint should return current configuration values."""
        response = client.get("/api/limits")
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["exec_timeout_s"] == config.exec_timeout_s
        assert data["compile_timeout_s"] == config.compile_timeout_s
        assert data["max_code_kb"] == config.max_code_kb
        assert data["runs_per_minute"] == config.runs_per_minute

    def test_limits_no_auth_required(self, client):
        """Limits endpoint should be public (no auth required)."""
        response = client.get("/api/limits")
        assert response.status_code == 200
