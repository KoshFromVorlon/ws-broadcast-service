import asyncio
import signal
import time
import logging
import sys
import os
from app.manager import manager

logger = logging.getLogger(__name__)


async def graceful_shutdown_task():
    """Логика плавного завершения работы."""
    if manager.is_shutting_down:
        return

    manager.is_shutting_down = True
    MAX_WAIT_TIME = 30 * 60  # 30 минут из ТЗ
    start_time = time.time()

    logger.info("SHUTDOWN: Received signal. Waiting for clients to disconnect...")

    while len(manager.active_connections) > 0:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_TIME:
            logger.warning("SHUTDOWN: Timeout reached. Forcing exit.")
            break

        logger.info(f"SHUTDOWN: Waiting for {len(manager.active_connections)} clients... ({int(elapsed)}s)")
        await asyncio.sleep(5)

    logger.info("SHUTDOWN: All clients disconnected. Exiting process.")

    # На Windows loop.stop() часто не срабатывает из-за особенностей Uvicorn
    # os._exit гарантирует немедленное завершение процесса воркера
    os._exit(0)
