import asyncio
import logging
from fastapi import FastAPI
from app.ws_handler import router, broadcast_periodic_notifications
from app.signals import setup_signal_handlers

logging.basicConfig(level=logging.INFO, format="%(process)d - %(asctime)s - %(message)s")

app = FastAPI(title="Graceful WebSocket Server")

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    # Настройка сигналов
    setup_signal_handlers()
    # Запуск фоновой рассылки
    asyncio.create_task(broadcast_periodic_notifications())
