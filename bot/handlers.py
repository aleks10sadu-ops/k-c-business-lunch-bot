"""
Обработчики сообщений Telegram-бота.

Обрабатывает команды и текстовые сообщения с меню.
"""

import os
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from bot.parser import parse_menu
from renderer.image_renderer import ImageRenderer
from config.loader import ConfigLoader


# Создаем router для обработчиков
router = Router()

# Глобальная переменная для хранения config_loader
# В production лучше использовать dependency injection через middleware
_config_loader: ConfigLoader = None


def set_config_loader(config_loader: ConfigLoader):
    """Устанавливает глобальный config_loader."""
    global _config_loader
    _config_loader = config_loader


def get_config_loader() -> ConfigLoader:
    """Получает глобальный config_loader."""
    if _config_loader is None:
        raise RuntimeError("Config loader не инициализирован")
    return _config_loader


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start."""
    welcome_text = (
        "👋 Привет! Я бот для генерации изображений меню бизнес-ланчей.\n\n"
        "📝 Отправь мне текст меню в следующем формате:\n\n"
        "ПН:\n"
        "1. БОРЩ [говядина, свёкла, сметана]\n"
        "2. ПЛОВ [рис, курица, морковь]\n\n"
        "ВТ:\n"
        "1. СУП ЛАПША [куриный бульон, лапша]\n"
        "2. ГРЕЧКА [гречка, курица]\n\n"
        "И так далее для всех дней недели.\n\n"
        "📅 Можно указать диапазон дат в любом месте:\n"
        "15.12–19.12 или С 15.12 по 19.12\n\n"
        "🚫 Для дней без бизнес-ланча:\n"
        "ПТ:\n"
        "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ\n\n"
        "или с датой:\n"
        "ПТ:\n"
        "ДО 12.01.26 БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ\n\n"
        "✨ После обработки ты получишь готовое изображение меню!"
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help."""
    help_text = (
        "📖 Справка по использованию бота:\n\n"
        "1. Отправь текст меню в формате:\n"
        "   ДЕНЬ:\n"
        "   1. НАЗВАНИЕ [описание]\n"
        "   2. НАЗВАНИЕ [описание]\n\n"
        "2. Поддерживаемые дни: ПН, ВТ, СР, ЧТ, ПТ\n\n"
        "3. Каждое блюдо должно иметь:\n"
        "   - Номер (1., 2., и т.д.)\n"
        "   - Название\n"
        "   - Описание в квадратных скобках []\n\n"
        "4. Бот автоматически сгенерирует изображение меню.\n\n"
        "📅 Диапазон дат:\n"
        "Укажите даты в формате: 15.12–19.12\n"
        "или: С 15.12 по 19.12\n\n"
        "🚫 Отсутствие бизнес-ланча:\n"
        "ПТ:\n"
        "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ\n\n"
        "С датой:\n"
        "ПТ:\n"
        "ДО 12.01.26 БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ"
    )
    await message.answer(help_text)


@router.message(F.text)
async def handle_menu_text(message: Message):
    """
    Обработчик текстовых сообщений с меню.
    
    Args:
        message: Сообщение от пользователя
    """
    text = message.text
    
    # Показываем индикатор печати
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    # Получаем config_loader
    config_loader = get_config_loader()
    
    # Загружаем настройки
    settings = config_loader.get_settings()
    zones = config_loader.get_zones()
    
    # Парсим меню
    menu_config = settings.get('menu', {})
    days = menu_config.get('days', [])
    max_dishes = menu_config.get('max_dishes_per_day', 7)
    
    parsed_data, error = parse_menu(text, days, max_dishes)
    
    if error:
        await message.answer(f"❌ Ошибка парсинга: {error}")
        return
    
    if not parsed_data:
        await message.answer("❌ Не удалось распарсить меню. Проверьте формат текста.")
        return
    
    # Генерируем изображение
    fonts_config = settings.get('fonts', {})
    layout_config = settings.get('layout', {})
    date_config = settings.get('date_block', {})
    warning_config = settings.get('warning_block', {})
    template_path = settings.get('template', {}).get('image', 'assets/template.png')
    output_path = settings.get('output', {}).get('path', 'output/result.png')
    
    renderer = ImageRenderer(
        template_path=template_path,
        zones=zones,
        fonts_config=fonts_config,
        layout_config=layout_config,
        warning_config=warning_config
    )
    
    error_msg = renderer.render(parsed_data, output_path, date_config, warning_config)
    
    if error_msg:
        await message.answer(f"❌ Ошибка генерации изображения: {error_msg}")
        return
    
    # Отправляем изображение пользователю
    if os.path.exists(output_path):
        photo = FSInputFile(output_path)
        await message.answer_photo(photo, caption="✨ Готово! Ваше меню:")
    else:
        await message.answer("❌ Изображение не было создано.")


async def setup_handlers(dp, config_loader: ConfigLoader):
    """
    Настраивает обработчики для диспетчера.
    
    Args:
        dp: Диспетчер aiogram
        config_loader: Загрузчик конфигурации
    """
    # Устанавливаем config_loader для использования в handlers
    set_config_loader(config_loader)
    
    dp.include_router(router)

