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
