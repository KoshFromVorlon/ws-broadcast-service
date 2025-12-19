import asyncio
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_shutting_down = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected. Active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Active: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            return

        # Создаем задачи для одновременной рассылки всем
        tasks = [connection.send_text(message) for connection in self.active_connections]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug("Failed to send message to a client, they might have disconnected.")


manager = ConnectionManager()
