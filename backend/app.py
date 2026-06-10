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


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "simplesc": check_simplesc()
    })


@app.route('/api/compile', methods=['POST'])
def compile_code():
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
