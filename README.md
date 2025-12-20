# FastAPI Graceful WebSocket Server

A production-ready FastAPI implementation of a WebSocket server with a custom graceful shutdown mechanism.

## Features

- **Connection Tracking**: Manages active WebSocket connections across multiple workers.
- **Real-time Notifications**: Periodic broadcast to all connected clients.
- **Graceful Shutdown**:
    - Intercepts `SIGINT` and `SIGTERM`.
    - Waits for all clients to disconnect naturally.
    - Enforces a hard timeout of 30 minutes.
    - Blocks new connections during the shutdown phase.

## Setup

1. Clone the repository.
    ```git
   git clone https://github.com/KoshFromVorlon/ws-broadcast-service.git
    ```
2. Install dependencies:
    ```bash
   pip install -r requirements.txt
    ```

3. Run the server with multiple workers:
    ```bash
   uvicorn app.main:app --workers 4
    ```

## How to Test

1. Connect to ws://localhost:8000/ws using a tool like wscat or a browser extension.

2. Observe periodic messages every 10 seconds.

3. Send a SIGINT to the server (Press Ctrl+C).

4. Notice that the server process stays alive as long as your WebSocket client is connected.

5. Disconnect the client and observe the server logs showing immediate shutdown.
