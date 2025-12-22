import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from starlette.websockets import WebSocketDisconnect

# Import the actual handler and the manager to use in assertions
from app.ws_handler import websocket_endpoint
from app.manager import manager


@pytest.mark.asyncio
async def test_websocket_connection_logic():
    """
    Test Case: Verify that the endpoint accepts connection and sends welcome message.
    Patches the manager directly inside the ws_handler module to ensure it's caught.
    """
    # 1. Create a mock websocket object
    mock_ws = AsyncMock()
    # Mock receive_text to raise Disconnect to break the infinite while loop
    mock_ws.receive_text.side_effect = WebSocketDisconnect(code=1000)

    # 2. Patch the manager where it is USED (in ws_handler)
    with patch("app.ws_handler.manager") as mocked_manager:
        mocked_manager.is_shutting_down = False
        mocked_manager.connect = AsyncMock()

        # 3. Call the handler
        try:
            await websocket_endpoint(mock_ws)
        except WebSocketDisconnect:
            pass

        # 4. Assertions
        mocked_manager.connect.assert_called_once()
        # Verify welcome message was sent through the mock_ws
        send_calls = [call.args[0] for call in mock_ws.send_text.call_args_list]
        assert any("Welcome!" in msg for msg in send_calls)


@pytest.mark.asyncio
async def test_shutdown_rejection_logic():
    """
    Test Case: Verify rejection when shutdown is active.
    """
    mock_ws = AsyncMock()
    with patch("app.ws_handler.manager") as mocked_manager:
        mocked_manager.is_shutting_down = True

        await websocket_endpoint(mock_ws)

        # Ensure it closed the connection with 1001
        mock_ws.close.assert_called_once_with(code=1001)


@pytest.mark.asyncio
async def test_manager_broadcast_logic():
    """
    Test Case: Verify Redis publishing via the manager.
    """
    with patch("app.manager.redis.from_url") as mock_redis_factory:
        mock_redis = AsyncMock()
        mock_redis_factory.return_value = mock_redis

        # Re-initialize or use the mocked client
        manager.redis_client = mock_redis
        await manager.broadcast("test_payload")

        mock_redis.publish.assert_called()


@pytest.mark.asyncio
async def test_manager_state():
    """
    Test Case: Verify local connection tracking.
    """
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()

    # Prevent the real redis listener from starting
    with patch.object(manager, 'redis_listener', return_value=AsyncMock()):
        await manager.connect(mock_ws)
        assert mock_ws in manager.active_connections

        manager.disconnect(mock_ws)
        assert mock_ws not in manager.active_connections
