"""
Testes para o endpoint POST /api/compile e o compiler.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import pytest
from app import app as flask_app
from compiler import compile_simples, CompileResult, _parse_errors


@pytest.fixture
def app():
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


class TestCompilerService:
    """Testes para compile_simples() (usa mock quando sem simplesc)."""

    def test_empty_code(self):
        """Código vazio deve retornar erro."""
        result = compile_simples("")
        assert not result.success
        assert len(result.errors) > 0
        assert "vazio" in result.errors[0]["message"].lower()

    def test_no_programa_keyword(self):
        """Código sem 'programa' deve retornar erro."""
        result = compile_simples("inteiro x\ninicio\nfim")
        assert not result.success

    def test_valid_mock_compile(self):
        """Código com 'programa' e 'fim' deve compilar (mock)."""
        code = "programa teste\n  inteiro x\ninicio\n  leia x\n  escreva x\nfim"
        result = compile_simples(code)
        assert result.success
        assert "section .data" in result.asm

    def test_error_parsing(self):
        """_parse_errors deve extrair linha e coluna."""
        stderr = "3:7: variavel 'y' nao declarada"
        errors = _parse_errors(stderr)
        assert len(errors) == 1
        assert errors[0]["line"] == 3
        assert errors[0]["column"] == 7
        assert "nao declarada" in errors[0]["message"]

    def test_error_fallback_format(self):
        """Formato sem coluna deve usar default column=0."""
        stderr = "5: erro sintatico"
        errors = _parse_errors(stderr)
        assert len(errors) >= 1
        error = next(e for e in errors if e["line"] == 5)
        assert error["column"] == 0 or error["column"] == 1


class TestCompileEndpoint:
    """Testes para POST /api/compile."""

    def test_no_code_field_returns_400(self, client):
        """Request sem 'code' deve retornar 400."""
        resp = client.post("/api/compile", json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert not data["success"]
        assert "obrigatório" in data["errors"][0]["message"]

    def test_missing_body_returns_400(self, client):
        """Request sem body deve retornar 400."""
        resp = client.post("/api/compile", data="not json", content_type="application/json")
        # Flask retorna 415 ou 400 dependendo da versão
        assert resp.status_code in (400, 415)

    def test_valid_code_returns_nasm(self, client):
        """Código válido deve retornar 200 com NASM."""
        code = "programa hello\ninicio\n  escreva 42\nfim"
        resp = client.post("/api/compile", json={"code": code})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"]
        assert len(data["asm"]) > 0

    def test_invalid_code_returns_422(self, client):
        """Código inválido deve retornar 422 com erros."""
        resp = client.post("/api/compile", json={"code": "isto nao eh codigo simples"})
        assert resp.status_code == 422
        data = resp.get_json()
        assert not data["success"]
        assert len(data["errors"]) > 0

    def test_oversized_code_returns_413(self, client):
        """Código > 64 KB deve retornar 413."""
        big_code = "a" * (64 * 1024 + 1)
        resp = client.post("/api/compile", json={"code": big_code})
        assert resp.status_code == 413

    def test_code_exactly_at_limit(self, client):
        """Código exatamente em 64 KB deve ser aceito."""
        limit_code = "a" * (64 * 1024)
        resp = client.post("/api/compile", json={"code": limit_code})
        assert resp.status_code != 413

    def test_health_endpoint(self, client):
        """GET /api/health deve retornar ok."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"
