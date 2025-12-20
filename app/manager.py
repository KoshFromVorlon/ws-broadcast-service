import asyncio
import logging
import redis.asyncio as redis
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.active_connections: Set[WebSocket] = set()
        self.is_shutting_down = False
        # Создаем клиент Redis. Он ленивый, ошибка будет только при попытке подключения.
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
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
        """Отправка сообщения через Redis для всех воркеров."""
        try:
            await self.redis_client.publish("notifications", message)
        except Exception:
            # Если Redis упал, шлем хотя бы локальным клиентам этого воркера
            await self._send_to_local_clients(message)

    async def _send_to_local_clients(self, message: str):
        """Физическая отправка сообщения клиентам этого процесса."""
        if not self.active_connections:
            return
        tasks = [conn.send_text(message) for conn in self.active_connections]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def redis_listener(self):
        """Подписка на канал Redis для синхронизации воркеров."""
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe("notifications")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._send_to_local_clients(message["data"])
        except Exception as e:
            logger.error(f"Redis connection failed: {e}. Running in local mode.")


manager = ConnectionManager()
