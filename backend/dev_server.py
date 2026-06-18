"""Dev server with WebSocket support via gevent."""
from gevent import monkey
monkey.patch_all()

from app import create_app

app = create_app()

if __name__ == "__main__":
    from gevent.pywsgi import WSGIServer
    http_server = WSGIServer(("127.0.0.1", 5000), app)
    print("Backend running at http://127.0.0.1:5000 (gevent + WebSocket)")
    http_server.serve_forever()
