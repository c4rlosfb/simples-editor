"""Tests for Prometheus metrics (metrics.py)."""

import json
from unittest.mock import patch

import pytest
from prometheus_client import REGISTRY


class TestMetricsDefinitions:
    """Tests for metric definitions."""

    def test_compile_duration_histogram(self):
        """compile_duration histogram should be registered."""
        from app.metrics import compile_duration
        assert compile_duration is not None
        assert "simples_compile_duration_seconds" in str(compile_duration)

    def test_execution_duration_histogram(self):
        """execution_duration histogram should be registered."""
        from app.metrics import execution_duration
        assert execution_duration is not None
        assert "simples_execution_duration_seconds" in str(execution_duration)

    def test_executions_total_counter(self):
        """executions_total counter should be registered."""
        from app.metrics import executions_total
        assert executions_total is not None
        assert "simples_executions" in str(executions_total)

    def test_compile_errors_total_counter(self):
        """compile_errors_total counter should be registered."""
        from app.metrics import compile_errors_total
        assert compile_errors_total is not None
        assert "simples_compile_errors" in str(compile_errors_total)

    def test_executions_stopped_counter(self):
        """executions_stopped counter should be registered."""
        from app.metrics import executions_stopped
        assert executions_stopped is not None
        assert "simples_executions_stopped" in str(executions_stopped)

    def test_active_sandboxes_gauge(self):
        """active_sandboxes gauge should be registered."""
        from app.metrics import active_sandboxes
        assert active_sandboxes is not None
        assert "simples_active_sandboxes" in str(active_sandboxes)

    def test_websocket_connections_gauge(self):
        """websocket_connections gauge should be registered."""
        from app.metrics import websocket_connections
        assert websocket_connections is not None
        assert "simples_websocket_connections" in str(websocket_connections)

    def test_metrics_blueprint_registered(self):
        """metrics_bp should be a valid blueprint."""
        from app.metrics import metrics_bp
        assert metrics_bp is not None
        assert metrics_bp.name == "metrics"


class TestMetricsEndpoint:
    """Tests for /metrics endpoint."""

    def test_metrics_endpoint_returns_prometheus_format(self, app):
        """GET /metrics should return Prometheus text format."""
        with app.test_client() as client:
            response = client.get("/metrics")
            assert response.status_code == 200
            # Prometheus format contains HELP and TYPE lines
            text = response.data.decode("utf-8")
            assert "HELP" in text or "TYPE" in text or "simples_" in text

    def test_metrics_endpoint_content_type(self, app):
        """GET /metrics should return text/plain content type."""
        with app.test_client() as client:
            response = client.get("/metrics")
            assert response.status_code == 200
            assert "text/plain" in response.content_type

    def test_metrics_includes_registered_metrics(self, app):
        """Metrics endpoint should expose registered metrics."""
        # Increment some counters to ensure they appear
        from app.metrics import executions_total, compile_errors_total
        executions_total.labels(outcome="success").inc()
        compile_errors_total.labels(phase="lexer").inc()

        with app.test_client() as client:
            response = client.get("/metrics")
            text = response.data.decode("utf-8")
            assert "simples_executions_total" in text
            assert "simples_compile_errors_total" in text
