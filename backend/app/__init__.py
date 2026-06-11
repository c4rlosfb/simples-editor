"""Application factory for the Simples Editor backend."""

from flask import Flask

from app.config import config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    app.config["SECRET_KEY"] = config.supabase_jwt_secret
    app.config["MAX_CONTENT_LENGTH"] = config.max_code_bytes + 1024

    # Register extensions & routes
    _register_extensions(app)
    _register_routes(app)

    return app


def _register_extensions(app: Flask) -> None:
    """Initialize Flask extensions."""
    from app.limits import limiter
    limiter.init_app(app)


def _register_routes(app: Flask) -> None:
    """Register REST routes and WebSocket handlers."""
    from app.routes import routes_bp
    app.register_blueprint(routes_bp)

    from app.metrics import metrics_bp
    app.register_blueprint(metrics_bp)

    from app.ws_handler import register_ws
    register_ws(app)
