import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.manager import manager

client = TestClient(app)


def test_websocket_echo():
    """Проверка базового соединения и эхо-ответа."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert "Echo: ping" in data


def test_shutdown_rejection():
    """Проверка, что сервер отклоняет новых клиентов при выключении."""
    manager.is_shutting_down = True
    try:
        with pytest.raises(Exception):
            with client.websocket_connect("/ws"):
                pass
    finally:
        manager.is_shutting_down = False
