import asyncio
import logging
import os
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def test_notification_task():
    """Периодическая рассылка раз в 10 секунд (только 1 воркер шлет в Redis)."""
    while not manager.is_shutting_down:
        await asyncio.sleep(10)
        # Блокировка, чтобы не спамить из всех воркеров сразу
        lock = await manager.redis_client.set("notif_lock", "active", ex=9, nx=True)
        if lock:
            pid = os.getpid()
            msg = f"[{datetime.now().strftime('%H:%M:%S')}] SYSTEM (PID:{pid}): Periodic Notification"
            await manager.broadcast(msg)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    await manager.connect(websocket)
    pid = os.getpid()

    try:
        await websocket.send_text(f"Connected to worker PID: {pid}")
        while True:
            data = await websocket.receive_text()
            # Рассылаем всем через Redis
            await manager.broadcast(f"User (via PID:{pid}) says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error on PID {pid}: {e}")
        manager.disconnect(websocket)
