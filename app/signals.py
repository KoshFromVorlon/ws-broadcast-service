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
    logger.info(f"[PID:{pid}] SHUTDOWN STARTED: Waiting for clients to disconnect...")

    # Останавливаем слушатель Redis
    if manager.pubsub_task:
        manager.pubsub_task.cancel()

    try:
        # Цикл ожидания: максимум 30 минут (1800 секунд)
        for i in range(1801):
            count = len(manager.active_connections)
            if count == 0:
                logger.info(f"[PID:{pid}] SHUTDOWN: All clients gone.")
                break

            if i % 5 == 0:  # Логируем каждые 5 секунд
                logger.info(f"[PID:{pid}] SHUTDOWN: {count} clients remain... ({i}s passed)")

            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        logger.info(f"[PID:{pid}] SHUTDOWN: Success. Force exiting process.")
        # Эти две строки гарантируют оживление терминала
        os.kill(pid, signal.SIGTERM)
        os._exit(0)
