import asyncio
import logging
import os
import redis.asyncio as redis
from typing import Set, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Constants to avoid "Magic Strings" and Numbers
DEFAULT_REDIS_URL = "redis://localhost:6379"
REDIS_CHANNEL = "notifications"


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_shutting_down = False
        self.redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL)
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        """Accepts a new connection and registers it locally."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Local active: {len(self.active_connections)}")

        # Ensure Redis listener is running if not already started
        if self.pubsub_task is None or self.pubsub_task.done():
            self.pubsub_task = asyncio.create_task(self.redis_listener())

    def disconnect(self, websocket: WebSocket):
        """Removes a connection from the local registry."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Local active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Publishes a message to Redis channel to reach all workers."""
        try:
            await self.redis_client.publish(REDIS_CHANNEL, message)
        except Exception as e:
            logger.error(f"Redis publish failed: {e}. Falling back to local broadcast.")
            await self._send_to_local_clients(message)

    async def _send_to_local_clients(self, message: str):
        """Sends a message directly to clients connected to THIS specific worker."""
        if not self.active_connections:
            return
        # Using gather with return_exceptions to ensure one failed socket doesn't kill the loop
        tasks = [conn.send_text(message) for conn in self.active_connections]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def redis_listener(self):
        """Subscribes to Redis and forwards messages to local clients."""
        pubsub = self.redis_client.pubsub()
        try:
            async with pubsub as p:
                await p.subscribe(REDIS_CHANNEL)
                async for message in p.listen():
                    # Stop listening if the worker is in shutdown mode
                    if self.is_shutting_down:
                        break
                    if message["type"] == "message":
                        await self._send_to_local_clients(message["data"])
        except Exception as e:
            if not self.is_shutting_down:
                logger.error(f"Redis listener error: {e}")


# Global instance of the manager
manager = ConnectionManager()
