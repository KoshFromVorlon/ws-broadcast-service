# FastAPI Graceful WebSocket Service

A production-ready FastAPI implementation of a WebSocket server designed for high availability and reliability. This
service supports cross-process synchronization and a sophisticated graceful shutdown mechanism.

## 🚀 Key Features

* **Multi-worker Architecture**: Engineered to work with multiple Uvicorn workers, ensuring scalability.
* **Redis Synchronization**: Uses **Redis Pub/Sub** to synchronize notifications across independent worker processes.
* **Cross-Platform Compatibility**: Custom signal handling for both **Linux (POSIX)** and **Windows**, addressing
  platform-specific event loop limitations.
* **Advanced Graceful Shutdown**:
* Intercepts `SIGINT` and `SIGTERM`.
* Rejects new connections immediately upon shutdown signal.
* Waits for active clients to disconnect naturally.
* Enforces a **30-minute hard timeout** as a safety buffer.


* **Real-time Broadcasting**: Periodic automated notifications and on-demand broadcasting via HTTP API.

## 🛠 Tech Stack

* **FastAPI**: Modern, high-performance web framework.
* **Redis**: Message broker for inter-process communication.
* **Docker & Docker Compose**: For seamless deployment and environment consistency.
* **Pytest**: Comprehensive test suite for WebSocket lifecycle and manager logic.

## 📦 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/KoshFromVorlon/ws-broadcast-service.git
cd ws-broadcast-service
```

### 2. Environment Setup

**Local Manual Setup:**

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the server:

```bash
uvicorn app.main:app --workers 4
```

## 🧪 How to Test

### 1. Connect via WebSocket

Use a tool like [wscat](https://github.com/websockets/wscat) or a browser extension (e.g., "WebSocket Test Client"):

* **URL**: `ws://localhost:8000/ws`

### 2. Observe Broadcasting

Once connected, you will receive a **"Periodic Test Notification"** every 10 seconds.

### 3. Test Graceful Shutdown

1. Connect one or more clients.
2. Press `Ctrl+C` in the server terminal.
3. **Observe**: The server logs `SHUTDOWN: Waiting for clients...` but remains active.
4. **Observe**: Try to connect a new client; the connection will be rejected.
5. Disconnect your active clients.
6. **Observe**: The server process terminates immediately after the last client leaves.

## 🧠 Architecture Explanation

* **Connection Management**: Unlike a simple list, we use a `ConnectionManager` with a `Set` for complexity in
  connection tracking.
* **Worker Isolation**: Since each Uvicorn worker is a separate OS process, they don't share memory. We solved the "
  Broadcast Dilemma" by implementing a Redis Pub/Sub layer. When a notification is triggered, it is published to Redis
  and consumed by all active workers simultaneously.
* **Signal Handling**: We use a `lifespan` context manager to handle startup and shutdown tasks. For Windows support, we
  utilize `signal.signal`, while for Linux, we use the more efficient `loop.add_signal_handler`.

## 📈 Testing

Run the automated test suite to verify connection handling and shutdown logic:

```bash
pytest
```

