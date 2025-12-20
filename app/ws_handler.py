import asyncio
import logging
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def test_notification_task():
    """Фоновая задача рассылки уведомлений каждые 10 секунд (по ТЗ)."""
    while not manager.is_shutting_down:
        await asyncio.sleep(10)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await manager.broadcast(f"{current_time}: Periodic Test Notification")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Ждем сообщение от клиента и отвечаем эхом
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        manager.disconnect(websocket)
