import asyncio
import signal
import time
import logging
from app.manager import manager

logger = logging.getLogger(__name__)


async def graceful_shutdown_task():
    manager.is_shutting_down = True
    MAX_WAIT_TIME = 30 * 60  # 30 минут
    start_time = time.time()

    logger.info("Shutdown signal received. Waiting for WebSocket clients to disconnect...")

    while len(manager.active_connections) > 0:
        elapsed = time.time() - start_time
        if elapsed > MAX_WAIT_TIME:
            logger.warning("Shutdown timeout reached. Forcing exit.")
            break

        logger.info(f"Waiting for {len(manager.active_connections)} clients... ({int(elapsed)}s elapsed)")
        await asyncio.sleep(5)

    logger.info("Graceful shutdown complete.")
    loop = asyncio.get_event_loop()
    loop.stop()


def setup_signal_handlers():
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown_task()))
