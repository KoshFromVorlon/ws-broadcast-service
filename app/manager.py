import asyncio
import logging
import os
import redis.asyncio as redis
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Управляет WebSocket-соединениями и синхронизацией через Redis Pub/Sub."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_shutting_down = False
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub_task = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Local active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Local active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Публикует сообщение в Redis для всех воркеров."""
        try:
            await self.redis_client.publish("notifications", message)
        except Exception as e:
            logger.error(f"Redis publish failed: {e}. Falling back to local broadcast.")
            await self._send_to_local_clients(message)

    async def _send_to_local_clients(self, message: str):
        """Отправляет сообщение только клиентам, подключенным к этому процессу."""
        if not self.active_connections:
            return
        tasks = [conn.send_text(message) for conn in self.active_connections]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def redis_listener(self):
        """Фоновый процесс прослушивания Redis для синхронизации воркеров."""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("notifications")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._send_to_local_clients(message["data"])
        except Exception as e:
            logger.error(f"Redis listener error: {e}. Worker is isolated.")


manager = ConnectionManager()
