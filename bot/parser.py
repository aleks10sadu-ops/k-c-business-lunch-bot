"""
Парсер текста меню бизнес-ланчей.

Обрабатывает входной текст, извлекает блюда по дням недели,
диапазон дат и состояние "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ".
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class DayMenu:
    """Модель данных для дня недели."""
    status: str  # "normal" | "disabled"
    disabled_until: Optional[str] = None  # Дата вида "12.01.26"
    dishes: List[Dict[str, str]] = None  # Список блюд
    
    def __post_init__(self):
        if self.dishes is None:
            self.dishes = []


class MenuParser:
    """Парсер меню с валидацией."""
    
    def __init__(self, days: List[str], max_dishes_per_day: int):
        """
        Инициализация парсера.
        
        Args:
            days: Список дней недели (например, ["ПН", "ВТ", "СР"])
            max_dishes_per_day: Максимальное количество блюд в день
        """
        self.days = days
        self.max_dishes_per_day = max_dishes_per_day
    
    def _extract_date_range(self, text: str) -> Optional[str]:
        """
        Извлекает диапазон дат из текста.
        
        Поддерживает форматы:
        - "15.12–19.12"
        - "С 15.12 по 19.12"
        - "15.12-19.12"
        
        Args:
            text: Входной текст
            
        Returns:
            Строка с диапазоном дат в формате "15.12–19.12" или None
        """
        # Паттерн для поиска диапазона дат
        # Поддерживает: dd.mm–dd.mm, dd.mm-dd.mm, С dd.mm по dd.mm
        patterns = [
            r'(\d{2}\.\d{2})\s*[-–—]\s*(\d{2}\.\d{2})',  # 15.12–19.12
            r'[Сс]\s+(\d{2}\.\d{2})\s+[Пп]о\s+(\d{2}\.\d{2})',  # С 15.12 по 19.12
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date1, date2 = match.groups()
                return f"{date1}–{date2}"
        
        return None
    
    def _parse_disabled_day(self, day_lines: List[str]) -> Tuple[Optional[str], bool]:
        """
        Парсит строки дня на предмет состояния "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ".
        
        Args:
            day_lines: Список строк дня
            
        Returns:
            Tuple[disabled_until, is_disabled]:
            - disabled_until: Дата до которой не будет бизнес-ланчей или None
            - is_disabled: True если день в состоянии "disabled"
        """
        text = ' '.join(day_lines).upper()
        
        # Проверяем наличие ключевой фразы
        if 'БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ' not in text:
            return None, False
        
        # Ищем дату в формате "ДО 12.01.26" или "12.01.26"
        date_patterns = [
            r'ДО\s+(\d{2}\.\d{2}\.\d{2})',  # ДО 12.01.26
            r'(\d{2}\.\d{2}\.\d{2})',  # 12.01.26 (без префикса)
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1), True
        
        return None, True
    
    def parse(self, text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Парсит текст меню с поддержкой дат и состояния "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ".
        
        Args:
            text: Входной текст меню
            
        Returns:
            Tuple[parsed_data, error_message]:
            - parsed_data: Dict с ключами-днями (DayMenu) и date_range или None
            - error_message: Текст ошибки или None
        """
        if not text or not text.strip():
            return None, "Пустой текст меню"
        
        # Извлекаем диапазон дат из всего текста
        date_range = self._extract_date_range(text)
        
        # Разбиваем текст на строки
        lines = text.strip().split('\n')
        
        result = {}
        current_day = None
        current_day_lines = []
        
        # Регулярное выражение для извлечения блюда
        # Формат: "1. НАЗВАНИЕ [описание]"
        dish_pattern = re.compile(r'^\d+\.\s*(.+?)\s*\[(.+?)\]$')
        
        # Паттерн для "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ"
        disabled_pattern = re.compile(r'БИЗНЕС\s+ЛАНЧЕЙ\s+НЕ\s+БУДЕТ', re.IGNORECASE)
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Проверяем, является ли строка заголовком дня
            # Формат: "ПН:" или "ПН"
            day_match = None
            for day in self.days:
                if line.startswith(day + ':') or (line == day):
                    day_match = day
                    break
            
            if day_match:
                # Сохраняем предыдущий день, если был
                if current_day is not None:
                    result[current_day] = self._process_day_lines(
                        current_day, current_day_lines, dish_pattern, disabled_pattern
                    )
                
                current_day = day_match
                current_day_lines = []
                continue
            
            # Если текущий день не установлен, пропускаем строку
            if current_day is None:
                continue
            
            # Добавляем строку к текущему дню
            current_day_lines.append(line)
        
        # Обрабатываем последний день
        if current_day is not None:
            result[current_day] = self._process_day_lines(
                current_day, current_day_lines, dish_pattern, disabled_pattern
            )
        
        # Валидация: проверяем, что все дни корректны
        invalid_days = set(result.keys()) - set(self.days)
        if invalid_days:
            return None, f"Обнаружены некорректные дни: {', '.join(invalid_days)}"
        
        # Валидация: проверяем блюда в обычных днях
        for day, day_menu in result.items():
            if day_menu.status == "normal":
                for dish in day_menu.dishes:
                    if not dish.get("title") or not dish.get("desc"):
                        return None, f"У блюда в дне {day} отсутствует название или описание"
                
                if len(day_menu.dishes) > self.max_dishes_per_day:
                    return None, (
                        f"Превышено максимальное количество блюд ({self.max_dishes_per_day}) "
                        f"для дня {day}"
                    )
        
        # Формируем результат
        parsed_result = {
            "date_range": date_range,
            **{day: result.get(day) for day in self.days}
        }
        
        return parsed_result, None
    
    def _process_day_lines(
        self,
        day: str,
        day_lines: List[str],
        dish_pattern: re.Pattern,
        disabled_pattern: re.Pattern
    ) -> DayMenu:
        """
        Обрабатывает строки одного дня.
        
        Args:
            day: Название дня
            day_lines: Список строк дня
            dish_pattern: Паттерн для поиска блюд
            disabled_pattern: Паттерн для поиска "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ"
            
        Returns:
            DayMenu объект
        """
        # Проверяем, есть ли блюда
        dishes = []
        for line in day_lines:
            dish_match = dish_pattern.match(line)
            if dish_match:
                title = dish_match.group(1).strip()
                description = dish_match.group(2).strip()
                dishes.append({
                    "title": title,
                    "desc": description
                })
        
        # Проверяем состояние "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ"
        disabled_until, is_disabled = self._parse_disabled_day(day_lines)
        
        # Если нет блюд и найден ключ "БИЗНЕС ЛАНЧЕЙ НЕ БУДЕТ" - день disabled
        if not dishes and is_disabled:
            return DayMenu(
                status="disabled",
                disabled_until=disabled_until,
                dishes=[]
            )
        
        # Обычный день с блюдами
        return DayMenu(
            status="normal",
            disabled_until=None,
            dishes=dishes
        )


def parse_menu(text: str, days: List[str], max_dishes_per_day: int) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Удобная функция для парсинга меню.
    
    Args:
        text: Текст меню
        days: Список дней недели
        max_dishes_per_day: Максимальное количество блюд в день
        
    Returns:
        Tuple[parsed_data, error_message]
        parsed_data содержит:
        - date_range: строка с диапазоном дат или None
        - дни недели: DayMenu объекты
    """
    parser = MenuParser(days, max_dishes_per_day)
    return parser.parse(text)

