"""
Aplicação Flask — endpoint POST /api/compile.

Recebe código SIMPLES, invoca o compilador,
e retorna NASM ou erros estruturados.
"""

from __future__ import annotations

import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from compiler import compile_simples

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/compile", methods=["POST"])
def compile_code():
    """
    POST /api/compile

    Request:  {"code": "<código SIMPLES>"}
    Response: {"success": true, "asm": "<NASM>"}
           ou {"success": false, "errors": [{line, column, message, phase}]}

    Validações:
    - Campo 'code' obrigatório
    - Tamanho máximo: 64 KB (RF17)
    - Timeout de compilação: 15s (RF15)
    """
    data = request.get_json(silent=True)

    # Validação de input
    if not data or "code" not in data:
        return jsonify({
            "success": False,
            "errors": [{
                "line": 0,
                "column": 0,
                "message": "Campo 'code' é obrigatório",
                "phase": "validation",
            }],
        }), 400

    code = data["code"]

    # Limite de tamanho — RF17
    if len(code.encode("utf-8")) > 64 * 1024:
        return jsonify({
            "success": False,
            "errors": [{
                "line": 0,
                "column": 0,
                "message": "Código excede limite de 64 KB",
                "phase": "validation",
            }],
        }), 413

    logger.info("Compilando %d bytes de código SIMPLES", len(code))

    result = compile_simples(code)

    if result.success:
        return jsonify({
            "success": True,
            "asm": result.asm,
        })

    return jsonify({
        "success": False,
        "errors": result.errors,
    }), 422
