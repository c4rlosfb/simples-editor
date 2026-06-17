"""Prometheus metrics definitions.

Defines the metrics exposed at /metrics as described in PRD §16.2.
Uses the prometheus_client library.
"""

from flask import Blueprint, Response

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# --- Histograms ---
compile_duration = Histogram(
    "simples_compile_duration_seconds",
    "Duration of compilation phases",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0),
    labelnames=["phase"],
)

execution_duration = Histogram(
    "simples_execution_duration_seconds",
    "Duration of binary execution",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 15.0),
    labelnames=["outcome"],
)

# --- Counters ---
executions_total = Counter(
    "simples_executions_total",
    "Total number of executions",
    labelnames=["outcome"],
)

compile_errors_total = Counter(
    "simples_compile_errors_total",
    "Total number of compilation errors",
    labelnames=["phase"],
)

executions_stopped = Counter(
    "simples_executions_stopped_total",
    "Total number of user-initiated stops",
)

# --- Gauges ---
active_sandboxes = Gauge(
    "simples_active_sandboxes",
    "Number of currently active sandbox containers",
)

websocket_connections = Gauge(
    "simples_websocket_connections",
    "Number of currently active WebSocket connections",
)

# --- Metrics blueprint ---
metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
