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
    Periodic notification task sent to all active clients (TZ requirement).
    Uses a Redis lock to ensure only one of the four workers sends the message.
    """
    while not manager.is_shutting_down:
        await asyncio.sleep(10)

        # Atomic Redis lock for 9 seconds to prevent duplicate messages from multiple workers
        lock_acquired = await manager.redis_client.set(
            "notification_lock", "active", ex=9, nx=True
        )

        if lock_acquired:
            current_time = datetime.now().strftime("%H:%M:%S")
            pid = os.getpid()
            # Global broadcast via Redis Pub/Sub
            await manager.broadcast(
                f"[{current_time}] SYSTEM (PID:{pid}): Periodic Notification (Every 10s)"
            )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Reject new connections if the shutdown process has been initiated
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    # Register the new connection
    await manager.connect(websocket)
    pid = os.getpid()

    try:
        # 1. Welcome message sent upon connection (full info)
        welcome_time = datetime.now().strftime('%H:%M:%S')
        await websocket.send_text(
            f" Welcome! Connected to Worker [PID: {pid}] at {welcome_time}. "
            f"Commands: 'test' or 'ping' for status check."
        )

        while True:
            # Wait for incoming client messages
            data = await websocket.receive_text()

            # 2. Command handling (on-demand notifications per TZ requirement)
            if data.lower() in ["test", "ping"]:
                current_time = datetime.now().strftime('%H:%M:%S')
                await manager.broadcast(
                    f"[{current_time}] TEST REQUEST from Client on PID:{pid}: System is Active"
                )
            else:
                # 3. Standard broadcast of user messages
                await manager.broadcast(f"User (via PID:{pid}) says: {data}")

    except WebSocketDisconnect:
        # Remove client from the local manager upon disconnection
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WS Error on PID {pid}: {e}")
        manager.disconnect(websocket)
