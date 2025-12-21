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
    Периодическая рассылка уведомлений всем активным клиентам (требование ТЗ).
    Использует Redis lock, чтобы только один воркер из четырех отправлял сообщение.
    """
    while not manager.is_shutting_down:
        await asyncio.sleep(10)

        # Атомарная блокировка в Redis на 9 секунд, чтобы избежать дублей от разных воркеров
        lock_acquired = await manager.redis_client.set(
            "notification_lock", "active", ex=9, nx=True
        )

        if lock_acquired:
            current_time = datetime.now().strftime("%H:%M:%S")
            pid = os.getpid()
            # Глобальный broadcast через Redis
            await manager.broadcast(
                f"[{current_time}] SYSTEM (PID:{pid}): Periodic Notification (Every 10s)"
            )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Если инициирован процесс завершения, отклоняем новые подключения
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    # Регистрируем новое соединение
    await manager.connect(websocket)
    pid = os.getpid()

    try:
        # 1. Приветственное сообщение при подключении (полная информация)
        welcome_time = datetime.now().strftime('%H:%M:%S')
        await websocket.send_text(
            f" Welcome! Connected to Worker [PID: {pid}] at {welcome_time}. "
            f"Commands: 'test' or 'ping' for status check."
        )

        while True:
            # Ожидание сообщения от клиента
            data = await websocket.receive_text()

            # 2. Обработка команд (уведомление по запросу согласно ТЗ)
            if data.lower() in ["test", "ping"]:
                current_time = datetime.now().strftime('%H:%M:%S')
                await manager.broadcast(
                    f"[{current_time}] TEST REQUEST from Client on PID:{pid}: System is Active"
                )
            else:
                # 3. Обычный broadcast пользовательского сообщения
                await manager.broadcast(f"User (via PID:{pid}) says: {data}")

    except WebSocketDisconnect:
        # Удаляем клиента из списка при отключении
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error on PID {pid}: {e}")
        manager.disconnect(websocket)
