"""Pytest fixtures for backend tests."""

import json
import time
from unittest.mock import MagicMock, patch

import jwt
import pytest

from app.auth import verify_jwt, AuthError
from app.config import config


TEST_JWT_SECRET = "test-secret-key-for-testing"
TEST_USER_ID = "test-user-uuid-12345"


def create_test_jwt(
    user_id: str = TEST_USER_ID,
    email: str = "test@example.com",
    expired: bool = False,
) -> str:
    """Create a test JWT for testing purposes."""
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(time.time()) - 10,
        "exp": int(time.time()) - 5 if expired else int(time.time()) + 3600,
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def patch_config():
    """Override JWT secret in config for tests."""
    original_secret = config.supabase_jwt_secret
    config.supabase_jwt_secret = TEST_JWT_SECRET
    yield
    config.supabase_jwt_secret = original_secret


@pytest.fixture
def valid_jwt():
    """Fixture: a valid test JWT."""
    return create_test_jwt()


@pytest.fixture
def expired_jwt():
    """Fixture: an expired test JWT."""
    return create_test_jwt(expired=True)


@pytest.fixture
def app():
    """Fixture: Flask test application."""
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    """Fixture: Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_header(valid_jwt):
    """Fixture: Authorization header with valid JWT."""
    return {"Authorization": f"Bearer {valid_jwt}"}


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for compiler tests."""
    with patch("app.compiler.subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_docker_client():
    """Mock docker.from_env() for execution tests."""
    with patch("app.execution.docker.from_env") as mock_from_env:
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        yield mock_client
