import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Set

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Новое подключение. Всего клиентов: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Клиент отключился. Осталось клиентов: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()
app = FastAPI()


@app.on_event("startup")
async def startup_event():
    async def send_periodic_notifications():
        while True:
            await asyncio.sleep(10)
            if manager.active_connections:
                # Добавляем текущее время до секунд
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await manager.broadcast(f"Ping: Сервер работает ({now})")

    asyncio.create_task(send_periodic_notifications())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await websocket.send_text(f"Вы отправили: {data} ({now})")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
