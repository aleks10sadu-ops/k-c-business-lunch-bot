"""
Главный файл запуска Telegram-бота.

Инициализирует бота, загружает конфигурацию и запускает polling.
"""

import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.handlers import setup_handlers
from config.loader import ConfigLoader


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота."""
    try:
        # Загружаем конфигурацию
        logger.info("Загрузка конфигурации...")
        config_loader = ConfigLoader()
        config_loader.load()
        
        # Получаем токен бота
        bot_token = config_loader.get_bot_token()
        logger.info("Конфигурация загружена успешно")
        
        # Инициализируем бота и диспетчер
        # В aiogram 3.7.0+ нужно использовать default для parse_mode
        bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        dp = Dispatcher()
        
        # Настраиваем обработчики
        logger.info("Настройка обработчиков...")
        await setup_handlers(dp, config_loader)
        
        # Храним config_loader в диспетчере для доступа в handlers
        dp["config_loader"] = config_loader
        
        # Запускаем polling
        logger.info("Запуск бота...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        raise
    finally:
        if 'bot' in locals():
            await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

