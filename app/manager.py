import asyncio
import logging
import os
import redis.asyncio as redis
from typing import Set, Optional
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_shutting_down = False
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
        self.pubsub_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Local active: {len(self.active_connections)}")

        # ГЛАВНОЕ: Запускаем слушатель Redis, если он еще не активен
        if self.pubsub_task is None or self.pubsub_task.done():
            self.pubsub_task = asyncio.create_task(self.redis_listener())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Local active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Публикует сообщение в Redis для всех воркеров."""
        try:
            await self.redis_client.publish("notifications", message)
        except Exception as e:
            logger.error(f"Redis publish failed: {e}. Falling back to local.")
            await self._send_to_local_clients(message)

    async def _send_to_local_clients(self, message: str):
        """Прямая отправка клиентам этого конкретного процесса."""
        if not self.active_connections:
            return
        tasks = [conn.send_text(message) for conn in self.active_connections]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def redis_listener(self):
        """Слушает канал Redis и пересылает сообщения локальным клиентам."""
        pubsub = self.redis_client.pubsub()
        try:
            async with pubsub as p:
                await p.subscribe("notifications")
                async for message in p.listen():
                    if self.is_shutting_down:
                        break
                    if message["type"] == "message":
                        await self._send_to_local_clients(message["data"])
        except Exception as e:
            if not self.is_shutting_down:
                logger.error(f"Redis listener error: {e}")


manager = ConnectionManager()
