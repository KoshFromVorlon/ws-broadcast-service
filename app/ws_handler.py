import asyncio
import logging
import os  # Добавляем для получения PID
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def test_notification_task():
    """Фоновая задача для рассылки уведомлений."""
    while not manager.is_shutting_down:
        await asyncio.sleep(10)

        # Используем распределенную блокировку в Redis,
        # чтобы только ОДИН воркер делал рассылку раз в 10 секунд
        lock_acquired = await manager.redis_client.set(
            "notification_lock", "active", ex=1, nx=True
        )

        if lock_acquired:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pid = os.getpid()  # Получаем ID текущего процесса

            # Формируем информативное сообщение
            message = f"[{current_time}] Worker PID:{pid} sent: Periodic Test Notification"

            await manager.broadcast(message)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            pid = os.getpid()
            await websocket.send_text(f"Echo from PID:{pid}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error: {e}")
        manager.disconnect(websocket)
