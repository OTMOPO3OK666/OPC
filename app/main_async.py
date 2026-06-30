import asyncio
import logging

import signal
import sys

from app.opc_server import OPCServer


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция"""
    server = OPCServer()
    
    def signal_handler(sig, frame):
        logger.info("Получен сигнал завершения")
        asyncio.create_task(server.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Получен Ctrl+C")
        await server.stop()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Программа завершена")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)