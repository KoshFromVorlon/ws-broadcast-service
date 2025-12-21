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
    logger.info(f"[PID:{pid}] SHUTDOWN STARTED: Checking clients...")

    try:
        # Уменьшим время проверки до 1 секунды для отзывчивости
        for i in range(1800):  # 30 минут
            count = len(manager.active_connections)
            if count == 0:
                break
            if i % 5 == 0:  # Логируем каждые 5 секунд
                logger.info(f"[PID:{pid}] SHUTDOWN: {count} clients remain...")
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        logger.info(f"[PID:{pid}] SHUTDOWN: Success. Force exiting.")
        # Принудительно убиваем текущий процесс воркера
        # Это решит проблему "зависания" терминала на Windows
        os.kill(pid, signal.SIGTERM)
        os._exit(0)
