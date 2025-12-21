FastAPI Graceful WebSocket Service
A high-performance WebSocket server built with FastAPI, featuring multi-worker synchronization via Redis and a robust
graceful shutdown mechanism.

## Quick Start / Быстрый запуск

1. Clone the repository / Клонирование
   ```Bash
   git clone https://github.com/KoshFromVorlon/ws-broadcast-service.git
   cd ws-broadcast-service
   ```

2. Run the Service / Запуск сервиса
   # Option A: Docker Compose (Recommended / Рекомендуется)
   Best for testing multi-worker synchronization and full environment isolation.

   ```Bash
   docker-compose up --build
   ```
   # Option B: PyCharm Terminal (Local / Локально). Requires Redis running on localhost:6379.

   ```Bash
   pip install -r requirements.txt
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 --no-signal-handlers
   ```
## Testing / Тестирование
1. Connection / Подключение
URL: ws://127.0.0.1:8000/ws
Postman: New -> WebSocket Request. Set environment to "No environment" (top right).
Browser: Use "WebSocket Test Client" extension.

2. Features / Функционал
Broadcasting: Send any text to see it mirrored across all connected clients.
On-Demand Status: Send test or ping to trigger a system-wide notification.
Periodic Updates: The system sends automated notifications every 10 seconds.

## Graceful Shutdown / Плавное завершение
This project implements a sophisticated shutdown logic as required by the technical task:
1. Initiate: Press Ctrl+C in the terminal.

2. Behavior:
The server enters "Shutdown Mode" but remains active for existing clients.
Broadcasting continues to work for currently connected users.
New connection requests are rejected.
3. Termination: The process exits only when the last client disconnects or the 30-minute timeout is reached.

## Architecture
FastAPI: Manages the WebSocket lifecycle.
Redis Pub/Sub: Ensures all 4 workers receive and broadcast messages simultaneously.
Signal Handling: Custom logic for SIGINT/SIGTERM ensures stability on both Linux and Windows.