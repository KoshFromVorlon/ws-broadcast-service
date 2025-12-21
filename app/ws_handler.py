import asyncio
import logging
import os
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.manager import manager

router = APIRouter()
logger = logging.getLogger(__name__)


async def test_notification_task():
    """
    Фоновая задача теперь просто висит, не спамя сообщениями.
    Мы оставляем её пустой или удаляем вызовы broadcast,
    так как переходим на логику 'по запросу'.
    """
    while not manager.is_shutting_down:
        await asyncio.sleep(10)
        # Здесь больше нет автоматического broadcast, чтобы не загромождать окна


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    await manager.connect(websocket)
    pid = os.getpid()

    try:
        # 1. Приветственное сообщение с полной информацией при подключении
        welcome_time = datetime.now().strftime('%H:%M:%S')
        await websocket.send_text(
            f" Welcome! Connected to Worker [PID: {pid}] at {welcome_time}. "
            f"Type 'test' or 'ping' for global status check."
        )

        while True:
            data = await websocket.receive_text()

            # 2. Обработка команд 'test' или 'ping' (Уведомление по запросу)
            if data.lower() in ["test", "ping"]:
                current_time = datetime.now().strftime('%H:%M:%S')
                # Делаем глобальную рассылку всем клиентам
                await manager.broadcast(
                    f"[{current_time}]  TEST REQUEST from Client on PID:{pid}: System is Active"
                )
            else:
                # 3. Обычные сообщения от пользователей
                await manager.broadcast(f"User (via PID:{pid}) says: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error on PID {pid}: {e}")
        manager.disconnect(websocket)
