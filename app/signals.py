import asyncio
import logging
import os
import signal
from app.manager import manager

logger = logging.getLogger(__name__)

# Constants to avoid "Magic Numbers"
SHUTDOWN_TIMEOUT_SEC = 1800  # 30 minutes per TZ requirement
LOG_INTERVAL_SEC = 10  # Progress log frequency


async def graceful_shutdown_task():
    """
    Handles the graceful shutdown process for the worker.
    Ensures existing clients can finish their sessions before the process exits.
    """
    if manager.is_shutting_down:
        return

    manager.is_shutting_down = True
    pid = os.getpid()
    logger.info(f"[PID:{pid}] SHUTDOWN STARTED: Checking for active connections...")

    try:
        # TZ Requirement: Wait up to 30 minutes or until 0 clients are connected
        for seconds_passed in range(SHUTDOWN_TIMEOUT_SEC + 1):
            count = len(manager.active_connections)
            if count == 0:
                logger.info(f"[PID:{pid}] SHUTDOWN: All connections closed.")
                break

            # Log progress based on LOG_INTERVAL_SEC
            if seconds_passed % LOG_INTERVAL_SEC == 0:
                remaining = SHUTDOWN_TIMEOUT_SEC - seconds_passed
                logger.info(
                    f"[PID:{pid}] SHUTDOWN PROGRESS: {count} clients connected. "
                    f"{seconds_passed}s/{SHUTDOWN_TIMEOUT_SEC}s passed. "
                    f"Force shutdown in {remaining}s."
                )

            await asyncio.sleep(1)

    finally:
        logger.info(f"[PID:{pid}] SHUTDOWN: Finalizing exit.")

        # Forcefully terminate this specific worker process to release the terminal
        # os.kill sends the signal, and os._exit(0) ensures an immediate exit
        os.kill(pid, signal.SIGTERM)
        os._exit(0)
