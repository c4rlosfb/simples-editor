"""Tests for authentication module (auth.py)."""

import time
from unittest.mock import patch

import jwt
import pytest
from flask import g

from app.auth import (
    verify_jwt,
    require_auth,
    extract_user_id,
    hash_user_id,
    AuthError,
)
from app.config import config

from .conftest import TEST_JWT_SECRET, TEST_USER_ID, create_test_jwt


class TestVerifyJWT:
    """Tests for verify_jwt() function."""

    def test_valid_token(self):
        """A valid JWT should return the decoded payload."""
        token = create_test_jwt()
        payload = verify_jwt(token)
        assert payload["sub"] == TEST_USER_ID
        assert payload["email"] == "test@example.com"

    def test_expired_token(self):
        """An expired JWT should raise AuthError."""
        token = create_test_jwt(expired=True)
        with pytest.raises(AuthError) as exc:
            verify_jwt(token)
        assert "expired" in str(exc.value.message).lower()

    def test_invalid_token(self):
        """A malformed JWT should raise AuthError."""
        with pytest.raises(AuthError) as exc:
            verify_jwt("not-a-valid-token")
        assert "invalid" in str(exc.value.message).lower()

    def test_token_missing_sub_claim(self):
        """A JWT without 'sub' claim should raise AuthError."""
        payload = {"email": "test@example.com", "exp": int(time.time()) + 3600}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        with pytest.raises(AuthError):
            verify_jwt(token)

    def test_token_missing_exp_claim(self):
        """A JWT without 'exp' claim should raise AuthError."""
        payload = {"sub": TEST_USER_ID, "email": "test@example.com"}
        token = jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")
        with pytest.raises(AuthError):
            verify_jwt(token)

    def test_wrong_secret(self):
        """A JWT signed with a different secret should raise AuthError."""
        token = create_test_jwt()
        # Temporarily change config secret
        original = config.supabase_jwt_secret
        config.supabase_jwt_secret = "different-secret"
        try:
            with pytest.raises(AuthError):
                verify_jwt(token)
        finally:
            config.supabase_jwt_secret = original


class TestUtilityFunctions:
    """Tests for utility functions in auth.py."""

    def test_extract_user_id(self):
        """extract_user_id should return the 'sub' claim."""
        payload = {"sub": TEST_USER_ID, "email": "test@example.com"}
        assert extract_user_id(payload) == TEST_USER_ID

    def test_hash_user_id(self):
        """hash_user_id should return a deterministic 16-char hex string."""
        h1 = hash_user_id("user-123")
        h2 = hash_user_id("user-123")
        assert h1 == h2
        assert len(h1) == 16
        # Different inputs should yield different hashes
        h3 = hash_user_id("user-456")
        assert h1 != h3


class TestRequireAuthDecorator:
    """Tests for the @require_auth decorator."""

    def test_with_valid_header(self, app, valid_jwt):
        """A valid Authorization header should set g.user_id and g.jwt_payload."""
        with app.test_request_context(
            headers={"Authorization": f"Bearer {valid_jwt}"}
        ):
            # Create a simple test view
            def test_view():
                return f"user:{g.user_id}", 200

            decorated = require_auth(test_view)
            response, status = decorated()
            assert status == 200
            assert TEST_USER_ID in response

    def test_without_auth_header(self, app):
        """Missing Authorization header should return 401."""
        with app.test_request_context():
            @require_auth
            def test_view():
                return "ok", 200

            response, status = test_view()
            assert status == 401
            assert b"Missing or invalid" in response.data if hasattr(response, 'data') else True

    def test_with_invalid_token(self, app):
        """Invalid token should return 401."""
        with app.test_request_context(
            headers={"Authorization": "Bearer invalidtoken"}
        ):
            @require_auth
            def test_view():
                return "ok", 200

            response, status = test_view()
            assert status == 401
            assert b"error" in response.data if hasattr(response, 'data') else True
