"""
Модуль загрузки конфигурации.

Читает YAML файлы и предоставляет единый интерфейс для доступа к настройкам.
"""

import os
import yaml
from typing import Dict, Any


class ConfigLoader:
    """Класс для загрузки конфигурации из YAML файлов."""
    
    def __init__(self, config_dir: str = "config"):
        """
        Инициализация загрузчика конфигурации.
        
        Args:
            config_dir: Директория с конфигурационными файлами
        """
        self.config_dir = config_dir
        self.settings = {}
        self.zones = {}
    
    def load(self) -> None:
        """Загружает все конфигурационные файлы."""
        settings_path = os.path.join(self.config_dir, "settings.yaml")
        zones_path = os.path.join(self.config_dir, "zones.yaml")
        
        # Загружаем settings.yaml
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                self.settings = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Конфигурационный файл не найден: {settings_path}")
        
        # Загружаем zones.yaml
        if os.path.exists(zones_path):
            with open(zones_path, 'r', encoding='utf-8') as f:
                self.zones = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"Файл зон не найден: {zones_path}")
    
    def get_settings(self) -> Dict[str, Any]:
        """Возвращает настройки из settings.yaml."""
        return self.settings
    
    def get_zones(self) -> Dict[str, Dict]:
        """Возвращает зоны из zones.yaml."""
        return self.zones
    
    def get_bot_token(self) -> str:
        """
        Получает токен бота из переменной окружения.
        
        Returns:
            Токен бота
            
        Raises:
            ValueError: Если токен не установлен
        """
        token_env_key = self.settings.get('bot', {}).get('token_env', 'BOT_TOKEN')
        token = os.getenv(token_env_key)
        
        if not token:
            raise ValueError(
                f"Токен бота не найден в переменной окружения {token_env_key}. "
                f"Установите её перед запуском бота."
            )
        
        return token

