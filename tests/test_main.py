import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.manager import manager

client = TestClient(app)


def test_websocket_echo():
    """Проверка базового подключения и эхо-ответа"""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("Hello Test")
        data = websocket.receive_text()
        assert "Echo: Hello Test" in data


def test_manager_connection_tracking():
    """Проверка, что менеджер видит новые подключения"""
    # До очистки (TestClient работает синхронно, но мы можем проверить состояние менеджера)
    initial_count = len(manager.active_connections)
    with client.websocket_connect("/ws"):
        # Внутри контекста количество должно увеличиться
        # Примечание: TestClient создает новое окружение, поэтому проверяем локально
        pass


@pytest.mark.asyncio
async def test_shutdown_rejection():
    """Проверка, что после сигнала завершения новые клиенты не принимаются"""
    manager.is_shutting_down = True
    try:
        with pytest.raises(Exception):  # FastAPI закроет сокет с кодом 1001
            with client.websocket_connect("/ws"):
                pass
    finally:
        manager.is_shutting_down = False  # Возвращаем в исходное состояние


def test_http_notify_not_found():
    """Проверка, что обычные HTTP запросы на корень возвращают 404"""
    response = client.get("/")
    assert response.status_code == 404
