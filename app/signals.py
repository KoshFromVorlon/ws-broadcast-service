import asyncio
import time
import logging
import os
from app.manager import manager

logger = logging.getLogger(__name__)


async def graceful_shutdown_task():
    """Логика плавного завершения работы (лимит 30 минут)."""
    if manager.is_shutting_down:
        return

    manager.is_shutting_down = True
    MAX_WAIT = 30 * 60  # 30 минут согласно ТЗ
    start_time = time.time()

    logger.info("SHUTDOWN: Signal received. Waiting for clients to disconnect...")

    while len(manager.active_connections) > 0:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT:
            logger.warning("SHUTDOWN: 30-minute timeout reached. Forcing exit.")
            break

        logger.info(f"SHUTDOWN: Waiting for {len(manager.active_connections)} clients... ({int(elapsed)}s)")
        await asyncio.sleep(5)

    logger.info("SHUTDOWN: Complete. Exiting process.")
    # Принудительный выход для надежной остановки воркера на любой ОС
    os._exit(0)
