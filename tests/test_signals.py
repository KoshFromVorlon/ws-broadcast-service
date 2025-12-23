import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.signals import graceful_shutdown_task
from app.manager import manager


@pytest.mark.asyncio
async def test_graceful_shutdown_waits_for_clients():
    """Tests that shutdown task waits while connections are active."""
    manager.is_shutting_down = False
    mock_ws = MagicMock()
    manager.active_connections.add(mock_ws)

    # Mock os.kill and os._exit to prevent the test from actually killing the process
    with patch("os.kill"), patch("os._exit"), patch("asyncio.sleep", return_value=None) as mock_sleep:
        # Start shutdown in a background task
        shutdown_coro = asyncio.create_task(graceful_shutdown_task())

        # Give it a few cycles
        await asyncio.sleep(0.1)

        # Simulate client disconnecting
        manager.active_connections.clear()

        await shutdown_coro

        # Ensure it actually waited (called sleep)
        assert mock_sleep.called
        assert manager.is_shutting_down is True
