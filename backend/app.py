<<<<<<< HEAD
<<<<<<< HEAD
"""
Aplicação Flask do Simples Editor.

Exporta a factory ``create_app()`` que monta blueprints,
middleware e configurações do backend.
"""

from __future__ import annotations

import logging

from flask import Flask

from routes.health import bp as health_bp


def create_app() -> Flask:
    """Factory — cria e configura a instância da aplicação Flask."""
    app = Flask(__name__)

    # ── Logging ──────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ── Blueprints ───────────────────────────────────────────
    app.register_blueprint(health_bp)

    # ── Rota raiz (placeholder) ──────────────────────────────
    @app.route("/")
    def index():
        return {"name": "Simples Editor API", "version": "0.1.0"}

    return app


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug)
=======
import os
import subprocess
import tempfile
import shutil
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SIMPLESC = shutil.which('simplesc') or '/usr/local/bin/simplesc'
COMPILE_TIMEOUT = 15  # seconds


def parse_simplesc_output(stderr: str) -> list:
    """Parse simplesc error output into structured format."""
    errors = []
    for line in stderr.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Format: "linha:coluna: mensagem" or "linha: mensagem"
        parts = line.split(':', 2)
        try:
            line_num = int(parts[0].strip())
            if len(parts) >= 3:
                col = int(parts[1].strip())
                msg = parts[2].strip()
            else:
                col = 1
                msg = parts[1].strip() if len(parts) > 1 else line
            errors.append({
                "line": line_num,
                "column": col,
                "message": msg,
                "phase": "compiler"
            })
        except (ValueError, IndexError):
            errors.append({
                "line": 0,
                "column": 0,
                "message": line,
                "phase": "compiler"
            })
    return errors


def check_simplesc() -> bool:
    """Check if simplesc is available."""
    return shutil.which('simplesc') is not None or os.path.exists(SIMPLESC)

=======
import os
import json
import logging
import asyncio
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sock import Sock

from execution import CompilerService

app = Flask(__name__)
CORS(app)
sock = Sock(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

compiler_service = CompilerService()


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------
>>>>>>> origin/fix/issue-31

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
<<<<<<< HEAD
        "simplesc": check_simplesc()
=======
        "simplesc": shutil.which('simplesc') is not None,
        "nasm": shutil.which('nasm') is not None,
        "ld": shutil.which('i686-linux-gnu-ld') is not None,
>>>>>>> origin/fix/issue-31
    })


@app.route('/api/compile', methods=['POST'])
def compile_code():
<<<<<<< HEAD
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({"error": "Campo 'code' é obrigatório"}), 400

    code = data['code']
    if not code or not code.strip():
        return jsonify({"success": False, "errors": [
            {"line": 0, "column": 0, "message": "Código vazio", "phase": "parser"}
        ]})

    # Create temp directory for compilation
    tmpdir = tempfile.mkdtemp(prefix='simples_')
    try:
        source_path = os.path.join(tmpdir, 'programa.simples')
        output_path = os.path.join(tmpdir, 'programa.asm')

        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(code)

        # Run simplesc compiler
        try:
            result = subprocess.run(
                [SIMPLESC, source_path, '-o', output_path],
                capture_output=True, text=True,
                timeout=COMPILE_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            return jsonify({
                "success": False,
                "errors": [{
                    "line": 0, "column": 0,
                    "message": "Tempo de compilação excedido (15s)",
                    "phase": "compiler"
                }]
            })

        if result.returncode != 0:
            errors = parse_simplesc_output(result.stderr)
            return jsonify({
                "success": False,
                "errors": errors if errors else [{
                    "line": 0, "column": 0,
                    "message": result.stderr.strip() or "Erro desconhecido na compilação",
                    "phase": "compiler"
                }]
            })

        # Read generated NASM
        if os.path.exists(output_path):
            with open(output_path, 'r', encoding='utf-8') as f:
                asm_content = f.read()
        else:
            asm_content = result.stdout

        return jsonify({
            "success": True,
            "asm": asm_content
        })

    except FileNotFoundError:
        return jsonify({
            "success": False,
            "errors": [{
                "line": 0, "column": 0,
                "message": "Compilador simplesc não encontrado no servidor",
                "phase": "system"
            }]
        })
    except Exception as e:
        logger.error(f"Compilation error: {e}")
        return jsonify({
            "success": False,
            "errors": [{
                "line": 0, "column": 0,
                "message": f"Erro interno: {str(e)}",
                "phase": "system"
            }]
        })
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
>>>>>>> origin/fix/issue-21
=======
    """REST compile endpoint (compilation only, no execution)."""
    data = request.get_json()
    if not data or 'code' not in data:
        return jsonify({"error": "Campo 'code' eh obrigatorio"}), 400

    result = compiler_service.compile(data['code'])
    return jsonify(result)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@sock.route('/ws/run')
def ws_run(ws):
    """WebSocket endpoint: compile + execute with real-time event streaming."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Receive initial message with source code
        raw = ws.receive(timeout=10)
        if not raw:
            return

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            ws.send(json.dumps({"type": "error", "message": "JSON invalido"}))
            return

        code = payload.get('code', '')
        if not code:
            ws.send(json.dumps({"type": "error", "message": "Codigo vazio"}))
            return

        # Run pipeline + listen for stdin concurrently
        async def run_pipeline(ws, code):
            gen = compiler_service.compile_and_run(code)

            async def consume_events():
                async for event in gen:
                    ws.send(json.dumps(event))

            async def listen_stdin():
                while True:
                    try:
                        raw = ws.receive(timeout=30)
                        if not raw:
                            break
                        msg = json.loads(raw)
                        if msg.get("type") == "stdin":
                            data = msg.get("data", "")
                            if isinstance(data, str):
                                data = data.encode()
                            compiler_service.pty_strategy.send_stdin(data)
                        elif msg.get("type") == "stop":
                            compiler_service.pty_strategy.stop()
                            break
                    except Exception:
                        break

            event_task = asyncio.ensure_future(consume_events())
            stdin_task = asyncio.ensure_future(listen_stdin())

            done, pending = await asyncio.wait(
                [event_task, stdin_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

        loop.run_until_complete(run_pipeline(ws, code))

    except Exception as e:
        logger.exception("WebSocket error")
        try:
            ws.send(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
    finally:
        loop.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
>>>>>>> origin/fix/issue-31
