import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.ws_handler import router as ws_router, test_notification_task
from app.manager import manager

# Configure global logging with Process ID for multi-worker tracking
logging.basicConfig(
    level=logging.INFO,
    format="[PID:%(process)d] %(asctime)s - %(message)s"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    from app.signals import graceful_shutdown_task

    # Set up signal interception for graceful shutdown
    loop = asyncio.get_running_loop()

    def handle_exit():
        """Helper to trigger the async shutdown task."""
        asyncio.create_task(graceful_shutdown_task())

    for sig in (signal.SIGINT, signal.SIGTERM):
        if sys.platform != "win32":
            # POSIX-compliant signal handling (Linux/Docker)
            loop.add_signal_handler(sig, handle_exit)
        else:
            # Windows-compatible signal handling
            signal.signal(sig, lambda s, f: handle_exit())

    # Start background tasks
    manager.pubsub_task = asyncio.create_task(manager.redis_listener())
    periodic_task = asyncio.create_task(test_notification_task())

    yield

    # --- SHUTDOWN ---
    # Cleanup background tasks and close connections
    periodic_task.cancel()
    if manager.pubsub_task:
        manager.pubsub_task.cancel()

    # Ensure Redis connection is closed properly
    await manager.redis_client.close()


# Initialize FastAPI application with the defined lifespan
app = FastAPI(title="Graceful WS Server", lifespan=lifespan)
app.include_router(ws_router)
