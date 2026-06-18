"""Tests for rate limiting configuration (limits.py)."""

from unittest.mock import MagicMock, patch

import pytest


class TestLimiterConfig:
    """Tests for limiter configuration."""

    def test_limiter_created(self):
        """Limiter should be created with correct defaults."""
        from app.limits import limiter
        assert limiter is not None
        assert limiter._storage_uri == "memory://"

    def test_ip_limiter_created(self):
        """IP limiter should be created with correct defaults."""
        from app.limits import ip_limiter
        assert ip_limiter is not None
        assert ip_limiter._storage_uri == "memory://"

    def test_key_func_user_authenticated(self, app):
        """_key_func_user should return user:uid when authenticated."""
        from app.limits import _key_func_user
        with app.test_request_context():
            from flask import g
            g.user_id = "user-123"
            key = _key_func_user()
            assert key == "user:user-123"

    def test_key_func_user_unauthenticated(self, app):
        """_key_func_user should return ip:... when not authenticated."""
        from app.limits import _key_func_user
        with app.test_request_context():
            key = _key_func_user()
            assert key.startswith("ip:")

    def test_get_user_id_with_authenticated(self, app):
        """_get_user_id should return user_id from g."""
        from app.limits import _get_user_id
        with app.test_request_context():
            from flask import g
            g.user_id = "user-abc"
            assert _get_user_id() == "user-abc"

    def test_get_user_id_without_g(self):
        """_get_user_id should return None when no app context."""
        from app.limits import _get_user_id
        # Outside of app context, AttributeError is caught
        result = _get_user_id()
        assert result is None
