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

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "simplesc": shutil.which('simplesc') is not None,
        "nasm": shutil.which('nasm') is not None,
        "ld": shutil.which('i686-linux-gnu-ld') is not None,
    })


@app.route('/api/compile', methods=['POST'])
def compile_code():
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
        raw = ws.receive()
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

        # Run the full pipeline asynchronously
        async def run_pipeline():
            async for event in compiler_service.compile_and_run(code):
                ws.send(json.dumps(event))

        loop.run_until_complete(run_pipeline())

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
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
