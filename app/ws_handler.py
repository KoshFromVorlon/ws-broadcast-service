import asyncio
import logging
import os
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def test_notification_task():
    """Периодическая рассылка (уже использует broadcast)."""
    while not manager.is_shutting_down:
        await asyncio.sleep(10)
        # Блокировка в Redis, чтобы слал только один воркер
        lock_acquired = await manager.redis_client.set(
            "notification_lock", "active", ex=1, nx=True
        )
        if lock_acquired:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pid = os.getpid()
            # Глобальная рассылка через Redis
            await manager.broadcast(f"[{current_time}] SYSTEM (PID:{pid}): Periodic Notification")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    await manager.connect(websocket)
    pid = os.getpid()

    try:
        # Приветственное сообщение только подключившемуся
        await websocket.send_text(f"Connected to worker PID: {pid}")

        while True:
            data = await websocket.receive_text()

            # ДЕМОНСТРАЦИЯ BROADCAST:
            # Вместо прямого ответа (websocket.send_text),
            # мы отправляем сообщение в manager.broadcast
            broadcast_message = f"User (via PID:{pid}) says: {data}"

            # Это сообщение уйдет в Redis и вернется ВСЕМ клиентам на ВСЕХ воркерах
            await manager.broadcast(broadcast_message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        manager.disconnect(websocket)
