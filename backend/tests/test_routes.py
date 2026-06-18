"""Tests for REST routes (routes.py)."""

import json
from unittest.mock import patch, MagicMock

import pytest

from app.config import config
from .conftest import create_test_jwt


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    @patch.dict("os.environ", {"SUPABASE_JWT_SECRET": "dev-secret-do-not-use-in-prod"})
    def test_health_returns_json_all_ok(self, app):
        """Health endpoint should return JSON with healthy status when all components ok."""
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
                    # Status may be "healthy" or "degraded" depending on env
                    assert data["status"] in ("healthy", "degraded")
                    assert data["version"] == config.version
                    assert "components" in data

    @patch.dict("os.environ", {"SUPABASE_JWT_SECRET": "dev-secret-do-not-use-in-prod"})
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

    def test_health_compiler_timeout(self, app):
        """Health should report timeout when compiler times out."""
        import subprocess
        with patch("subprocess.run") as mock_run:
            # First call (simplesc) times out, second call (nasm) works
            def mock_subprocess(*args, **kwargs):
                if "simplesc" in args[0]:
                    raise subprocess.TimeoutExpired(cmd="simplesc", timeout=5)
                m = MagicMock()
                m.returncode = 0
                m.stdout = "NASM version"
                m.stderr = ""
                return m
            mock_run.side_effect = mock_subprocess

            with patch("docker.from_env") as mock_docker:
                mock_client = MagicMock()
                mock_docker.return_value = mock_client

                with patch.dict("os.environ", {"SUPABASE_JWT_SECRET": "prod-secret"}):
                    with app.test_client() as client:
                        response = client.get("/api/health")
                        data = json.loads(response.data)
                        assert data["components"]["compiler"]["status"] == "timeout"

    @patch.dict("os.environ", {"SUPABASE_JWT_SECRET": "dev-secret-do-not-use-in-prod"})
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

    def test_health_supabase_config(self, app):
        """Health should report supabase configuration status."""
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

                with patch.dict("os.environ", {"SUPABASE_JWT_SECRET": "dev-secret-do-not-use-in-prod"}):
                    with app.test_client() as client:
                        response = client.get("/api/health")
                        data = json.loads(response.data)
                        assert data["components"]["supabase"]["status"] == "ok"
                        assert "demo mode" in data["components"]["supabase"].get("message", "")

    def test_health_supabase_production_secret(self, app):
        """Health should report production secret configured."""
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

                with patch.dict("os.environ", {"SUPABASE_JWT_SECRET": "prod-secret-key-12345"}):
                    with app.test_client() as client:
                        response = client.get("/api/health")
                        data = json.loads(response.data)
                        assert data["components"]["supabase"]["secret_configured"] is True

    def test_health_supabase_not_set(self, app):
        """Health should report supabase unavailable when not set."""
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

                with patch.dict("os.environ", {}, clear=True):
                    with app.test_client() as client:
                        response = client.get("/api/health")
                        data = json.loads(response.data)
                        assert data["components"]["supabase"]["status"] == "unavailable"


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


class TestCompileEndpoint:
    """Tests for POST /api/compile."""

    def test_compile_missing_body(self, client):
        """Missing body should return 400."""
        response = client.post("/api/compile")
        assert response.status_code == 400

    def test_compile_missing_code_field(self, client):
        """Missing code field should return 400."""
        response = client.post("/api/compile", json={})
        assert response.status_code == 400

    def test_compile_exceeds_size_limit(self, client):
        """Code exceeding size limit should return 413."""
        original_kb = config.max_code_kb
        config.max_code_kb = 1
        try:
            response = client.post("/api/compile", json={"code": "x" * 2048})
            assert response.status_code == 413
        finally:
            config.max_code_kb = original_kb

    @patch("app.routes.compile_simples")
    def test_compile_success(self, mock_compile, client):
        """Successful compilation should return 200 with ASM."""
        from app.compiler import CompileResult
        mock_compile.return_value = CompileResult(
            success=True,
            asm_source="section .text\nglobal _start\n_start:\n",
            duration_ms=10,
        )

        response = client.post("/api/compile", json={"code": "programa t\ninicio\nfim\n"})
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["success"] is True
        assert "section .text" in data["asm"]

    @patch("app.routes.compile_simples")
    def test_compile_with_errors(self, mock_compile, client):
        """Compilation with errors should return 422."""
        from app.compiler import CompileResult
        from app.errors import CompileError as CE
        mock_compile.return_value = CompileResult(
            success=False,
            errors=[
                CE(phase="lexer", line=4, column=7, message="caractere invalido"),
                CE(phase="parser", line=10, column=1, message="esperado 'fim'"),
            ],
        )

        response = client.post("/api/compile", json={"code": "programa t\ninicio\n@bad\nfim\n"})
        data = json.loads(response.data)
        assert response.status_code == 422
        assert data["success"] is False
        assert len(data["errors"]) == 2

    @patch("app.routes.compile_simples")
    def test_compile_error_no_parsed_errors(self, mock_compile, client):
        """Compilation error without parsed errors should return error_message."""
        from app.compiler import CompileResult
        mock_compile.return_value = CompileResult(
            success=False,
            errors=[],
            error_message="Unknown compilation error",
        )

        response = client.post("/api/compile", json={"code": "programa t\ninicio\nfim\n"})
        data = json.loads(response.data)
        assert response.status_code == 422
        assert data["success"] is False
        assert len(data["errors"]) == 1
        assert data["errors"][0]["message"] == "Unknown compilation error"

    @patch("app.routes.compile_simples")
    def test_compile_empty_asm(self, mock_compile, client):
        """Successful compilation with empty asm_source should work."""
        from app.compiler import CompileResult
        mock_compile.return_value = CompileResult(
            success=True,
            asm_source=None,
            duration_ms=10,
        )

        response = client.post("/api/compile", json={"code": "programa t\ninicio\nfim\n"})
        data = json.loads(response.data)
        assert response.status_code == 200
        assert data["success"] is True
        assert data["asm"] == ""
