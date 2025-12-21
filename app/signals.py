import asyncio
import logging
import os
import signal
from app.manager import manager

logger = logging.getLogger(__name__)


async def graceful_shutdown_task():
    if manager.is_shutting_down:
        return

    manager.is_shutting_down = True
    pid = os.getpid()
    logger.info(f"[PID:{pid}] SHUTDOWN STARTED: Checking for active connections...")

    try:
        # ТЗ: Ждать до 30 минут (1800 сек) или пока не станет 0 клиентов
        for i in range(1801):
            count = len(manager.active_connections)
            if count == 0:
                logger.info(f"[PID:{pid}] SHUTDOWN: All connections closed.")
                break

            if i % 10 == 0:  # Лог каждые 10 секунд
                logger.info(f"[PID:{pid}] SHUTDOWN PROGRESS: {count} clients connected. {i}s/1800s passed.")

            await asyncio.sleep(1)

    finally:
        logger.info(f"[PID:{pid}] SHUTDOWN: Finalizing exit.")
        # Принудительно убиваем только этот воркер, чтобы освободить терминал
        os.kill(pid, signal.SIGTERM)
        os._exit(0)


