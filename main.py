from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
connections = set()


# HTTP-эндпоинт для корня
@app.get("/")
async def get():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket клиент</h1>
        <button onclick="connectWS()">Подключиться</button>
        <script>
            function connectWS() {
                const ws = new WebSocket("ws://127.0.0.1:8000/ws");
                ws.onopen = () => {
                    console.log("Соединение установлено");
                    ws.send("Привет сервер!");
                };
                ws.onmessage = (event) => {
                    console.log("Ответ:", event.data);
                    alert("Ответ от сервера: " + event.data);
                };
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Вы отправили: {data}")
    except WebSocketDisconnect:
        connections.remove(websocket)
