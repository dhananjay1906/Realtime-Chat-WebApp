"""Runs the app on a real uvicorn server so tests exercise genuine WebSocket traffic."""

import socket
import threading
import time

import httpx
import pytest
import uvicorn

from app.main import create_app


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(tmp_path):
    port = _free_port()
    app = create_app(db_path=str(tmp_path / "test.db"), static_dir=str(tmp_path / "no-dist"))
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    thread = threading.Thread(target=srv.run, daemon=True)
    thread.start()
    base = f"127.0.0.1:{port}"
    for _ in range(100):
        try:
            httpx.get(f"http://{base}/api/health")
            break
        except httpx.HTTPError:
            time.sleep(0.05)
    yield base
    srv.should_exit = True
    thread.join(timeout=5)
