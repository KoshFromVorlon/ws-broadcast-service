import asyncio
import time
import logging
from app.manager import manager

logger = logging.getLogger(__name__)


async def graceful_shutdown_task():
    manager.is_shutting_down = True
    MAX_WAIT = 30 * 60
    start_time = time.time()

    logger.info("SHUTDOWN: Ожидание отключения клиентов...")

    while len(manager.active_connections) > 0:
        if time.time() - start_time > MAX_WAIT:
            logger.warning("SHUTDOWN: Таймаут. Принудительный выход.")
            break

        logger.info(f"SHUTDOWN: Ждем {len(manager.active_connections)} клиентов...")
        await asyncio.sleep(5)

    logger.info("SHUTDOWN: Готов к выходу.")
    # На Windows/Uvicorn здесь лучше просто позволить процессу завершиться через sys.exit
    import os
    os._exit(0)
