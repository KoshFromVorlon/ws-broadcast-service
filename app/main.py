import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.ws_handler import router as ws_router, test_notification_task
from app.manager import manager

logging.basicConfig(
    level=logging.INFO,
    format="[PID:%(process)d] %(asctime)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    # Кроссплатформенная обработка сигналов
    if sys.platform == "win32":
        from app.signals import graceful_shutdown_task
        signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(graceful_shutdown_task()))
        signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(graceful_shutdown_task()))
    else:
        loop = asyncio.get_running_loop()
        from app.signals import graceful_shutdown_task
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(graceful_shutdown_task()))

    # Запуск фоновых задач
    manager.pubsub_task = asyncio.create_task(manager.redis_listener())
    periodic_task = asyncio.create_task(test_notification_task())

    yield

    # --- SHUTDOWN ---
    periodic_task.cancel()
    if manager.pubsub_task:
        manager.pubsub_task.cancel()
    await manager.redis_client.close()


app = FastAPI(title="Graceful WS Server", lifespan=lifespan)
app.include_router(ws_router)
