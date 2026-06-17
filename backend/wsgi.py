"""WSGI entry point for Gunicorn.

Uses the full application factory from the app/ package (not app_cli.py),
which registers REST routes, WebSocket handlers, rate limiting, and metrics.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
