import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.manager import manager

router = APIRouter()


async def broadcast_periodic_notifications():
    """Фоновая задача для рассылки уведомлений."""
    while not manager.is_shutting_down:
        await asyncio.sleep(10)
        if manager.active_connections:
            await manager.broadcast("Real-time notification: Server is still running")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    if manager.is_shutting_down:
        await websocket.close(code=1001)
        return

    await manager.connect(websocket)
    try:
        while True:
            # Слушаем сообщения от клиента (keep-alive)
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
