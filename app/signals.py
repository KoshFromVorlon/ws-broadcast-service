import asyncio
import logging
import os
import signal
from app.manager import manager

logger = logging.getLogger(__name__)


async def graceful_shutdown_task():
    # Если процесс уже в стадии закрытия, игнорируем повторные сигналы
    if manager.is_shutting_down:
        return

    manager.is_shutting_down = True
    pid = os.getpid()

    # ТЗ: Логирование начала процесса завершения
    logger.info(f"[PID:{pid}] SHUTDOWN MODE: Service remains active for existing clients.")

    try:
        # ТЗ: Цикл ожидания. 1800 итераций по 1 секунде = 30 минут.
        for i in range(1801):
            count = len(manager.active_connections)

            # ТЗ: Условие "Дождитесь, пока все клиенты отключатся"
            if count == 0:
                logger.info(f"[PID:{pid}] SHUTDOWN: All clients disconnected.")
                break

            # ТЗ: Логирование прогресса (каждые 10 секунд)
            if i % 10 == 0:
                remaining = 1800 - i
                logger.info(f"[PID:{pid}] SHUTDOWN: {count} clients remain. Force shutdown in {remaining}s.")

            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Error during shutdown loop: {e}")
    finally:
        # Теперь, когда клиентов нет или 30 минут вышло — зачищаем ресурсы
        if manager.pubsub_task:
            manager.pubsub_task.cancel()

        logger.info(f"[PID:{pid}] SHUTDOWN: Final exit.")

        # ТЗ: "Принудительно завершите работу".
        # os._exit гарантирует моментальное закрытие процесса и оживление терминала.
        os.kill(pid, signal.SIGTERM)
        os._exit(0)
