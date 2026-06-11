"""WebSocket handler for /ws/run.

Implements the WebSocket protocol defined in PRD §9.2.
Handles the full state machine (IDLE → COMPILING → EXECUTING → IDLE)
as described in PRD §9.2.3.

Message types (client → server):
  - compile_and_run { code: str }
  - stdin { data: str }
  - stop
  - ping

Message types (server → client):
  - compile_started
  - compile_error { phase, line, column, message }
  - asm_generated { asm: str }
  - assemble_error { stderr: str }
  - link_error { stderr: str }
  - exec_started
  - stdout { data: str }
  - stderr { data: str }
  - exit { code, duration_ms }
  - timeout { limit_s }
  - internal_error { message }
  - pong
"""

import asyncio
import json
import logging
import time
from enum import Enum
from pathlib import Path

from flask import request
from flask_sock import Sock, ConnectionClosed

from app.auth import verify_jwt, extract_user_id, AuthError
from app.compiler import CompilerService
from app.config import config
from app.execution import PtyExecutionStrategy, ExecutionResult
from app.metrics import (
    compile_duration,
    execution_duration,
    executions_total,
    compile_errors_total,
    executions_stopped,
    active_sandboxes,
    websocket_connections,
)
from app.validation import validate_code, ValidationError

logger = logging.getLogger("simples.ws")

sock = Sock()


class WSState(Enum):
    """WebSocket connection state machine states."""

    IDLE = "idle"
    COMPILING = "compiling"
    EXECUTING = "executing"


class ConnectionState:
    """Tracks state for a single WebSocket connection."""

    def __init__(self):
        self.state = WSState.IDLE
        self.user_id: str | None = None
        self.workdir: Path | None = None
        self.compiler: CompilerService = CompilerService()
        self._executor: PtyExecutionStrategy | None = None

    @property
    def executor(self) -> PtyExecutionStrategy:
        """Lazy executor initialization (Docker client not created until needed)."""
        if self._executor is None:
            self._executor = PtyExecutionStrategy()
        return self._executor


def register_ws(app):
    """Register WebSocket endpoint with the Flask app."""
    sock.init_app(app)

    @sock.route("/ws/run")
    def ws_run(ws):
        """WebSocket endpoint for compilation and execution."""
        websocket_connections.inc()
        conn = ConnectionState()

        try:
            # Authenticate on connect
            _authenticate_ws(ws, conn)

            # Main message loop
            for raw_message in ws:
                try:
                    msg = json.loads(raw_message)
                    msg_type = msg.get("type", "")

                    if msg_type == "compile_and_run":
                        _handle_compile_and_run(ws, conn, msg)
                    elif msg_type == "stdin":
                        _handle_stdin(ws, conn, msg)
                    elif msg_type == "stop":
                        _handle_stop(ws, conn)
                    elif msg_type == "ping":
                        _safe_send(ws, json.dumps({"type": "pong"}))
                    else:
                        logger.warning(
                            "unknown_message_type: type=%s, state=%s",
                            msg_type, conn.state.value,
                        )

                except json.JSONDecodeError:
                    _safe_send(ws, json.dumps({
                        "type": "internal_error",
                        "message": "Invalid JSON message",
                    }))
                except ConnectionClosed:
                    break

        except AuthError as e:
            _safe_send(ws, json.dumps({
                "type": "internal_error",
                "message": e.message,
            }))
        except Exception as e:
            logger.exception("ws_unexpected_error")
            _safe_send(ws, json.dumps({
                "type": "internal_error",
                "message": f"Unexpected error: {e}",
            }))
        finally:
            _cleanup_connection(conn)
            websocket_connections.dec()


def _authenticate_ws(ws, conn: ConnectionState) -> None:
    """Authenticate the WebSocket connection via JWT.

    Checks Sec-WebSocket-Protocol header first, then query param.
    """
    token = None

    # Try Sec-WebSocket-Protocol: bearer.<jwt>
    protocol_header = request.headers.get("Sec-WebSocket-Protocol", "")
    if protocol_header.startswith("bearer."):
        token = protocol_header[len("bearer."):]

    # Fallback to query param ?token=<jwt>
    if not token:
        token = request.args.get("token")

    if not token:
        raise AuthError("Authentication required")

    payload = verify_jwt(token)
    conn.user_id = extract_user_id(payload)
    logger.info("ws_authenticated user_id=%s", conn.user_id)


def _handle_compile_and_run(ws, conn: ConnectionState, msg: dict) -> None:
    """Handle compile_and_run message — the main execution flow.

    State: IDLE → COMPILING → EXECUTING → IDLE
    """
    if conn.state != WSState.IDLE:
        _safe_send(ws, json.dumps({
            "type": "internal_error",
            "message": f"Cannot start: currently {conn.state.value}",
        }))
        return

    code = msg.get("code", "")
    try:
        validate_code(code)
    except ValidationError as e:
        _safe_send(ws, json.dumps({"type": "compile_error", "message": e.message}))
        return

    conn.state = WSState.COMPILING
    _safe_send(ws, json.dumps({"type": "compile_started"}))

    # --- Compilation phase ---
    compile_start = time.monotonic()
    result = conn.compiler.compile(code, workdir=conn.workdir)
    compile_seconds = time.monotonic() - compile_start

    if not result.success:
        conn.state = WSState.IDLE

        if result.errors:
            # Send structured errors
            for err in result.errors:
                compile_errors_total.labels(phase=err.phase).inc()
            compile_duration.labels(phase="compile").observe(compile_seconds)
            _safe_send(ws, json.dumps({
                "type": "compile_error",
                "errors": [
                    {"phase": e.phase, "line": e.line, "column": e.column, "message": e.message}
                    for e in result.errors
                ],
            }))
        else:
            # Send unstructured error
            compile_duration.labels(phase="compile").observe(compile_seconds)
            _safe_send(ws, json.dumps({
                "type": "compile_error",
                "phase": "unknown",
                "line": 0,
                "column": 0,
                "message": result.error_message or "Unknown compilation error",
            }))
        return

    # Send NASM source
    compile_duration.labels(phase="compile").observe(compile_seconds)
    _safe_send(ws, json.dumps({"type": "asm_generated", "asm": result.asm_source}))
    conn.workdir = result.binary_dir

    # --- Execution phase ---
    conn.state = WSState.EXECUTING
    _safe_send(ws, json.dumps({"type": "exec_started"}))
    active_sandboxes.inc()

    try:
        # Run the execution in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        exec_result: ExecutionResult = loop.run_until_complete(
            conn.executor.execute(
                binary_dir=result.binary_dir,
                ws=ws,
                timeout_s=config.exec_timeout_s,
            )
        )
        loop.close()
    except Exception as e:
        logger.exception("execution_async_error")
        _safe_send(ws, json.dumps({"type": "internal_error", "message": f"Execution error: {e}"}))
        exec_result = ExecutionResult(exit_code=-1, duration_ms=0, timed_out=False)

    active_sandboxes.dec()
    conn.state = WSState.IDLE

    if exec_result.timed_out:
        execution_duration.labels(outcome="timeout").observe(exec_result.duration_ms / 1000.0)
        executions_total.labels(outcome="timeout").inc()
        _safe_send(ws, json.dumps({
            "type": "timeout",
            "limit_s": config.exec_timeout_s,
        }))
    else:
        outcome = "runtime_error" if exec_result.exit_code != 0 else "success"
        execution_duration.labels(outcome=outcome).observe(exec_result.duration_ms / 1000.0)
        executions_total.labels(outcome=outcome).inc()
        _safe_send(ws, json.dumps({
            "type": "exit",
            "code": exec_result.exit_code,
            "duration_ms": exec_result.duration_ms,
        }))


def _handle_stdin(ws, conn: ConnectionState, msg: dict) -> None:
    """Handle stdin message from client.

    Only valid in EXECUTING state. Discarded silently in other states per PRD §9.2.3.
    """
    if conn.state != WSState.EXECUTING:
        logger.warning("stdin_in_invalid_state: state=%s", conn.state.value)
        return

    data = msg.get("data", "")
    # Stdin is forwarded directly via the execution strategy's ws_to_pty,
    # which reads from the WebSocket. If the execution is running in a
    # different loop context, we handle it here.
    logger.debug("stdin_received data_len=%s", len(data))


def _handle_stop(ws, conn: ConnectionState) -> None:
    """Handle stop message from client.

    Only valid in EXECUTING state. Sends SIGTERM via the executor.
    """
    if conn.state != WSState.EXECUTING:
        logger.warning("stop_in_invalid_state: state=%s", conn.state.value)
        return

    executions_stopped.inc()
    # The execution strategy's ws_to_pty task handles the 'stop' message
    # by calling container.kill(SIGTERM). We send the stop signal through
    # the WebSocket (the ws_to_pty task picks it up).
    logger.info("user_stop_requested user_id=%s", conn.user_id)


def _cleanup_connection(conn: ConnectionState) -> None:
    """Clean up resources associated with a connection."""
    if conn.workdir and conn.workdir.exists():
        conn.compiler.cleanup(conn.workdir)


def _safe_send(ws, message: str) -> None:
    """Send a message, ignoring closed connection errors."""
    try:
        ws.send(message)
    except ConnectionClosed:
        pass
    except Exception:
        logger.debug("ws_send_failed")
