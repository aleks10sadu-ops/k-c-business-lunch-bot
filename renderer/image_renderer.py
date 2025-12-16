"""
Модуль генерации изображений меню.

Загружает шаблон, накладывает текст меню на заданные зоны
и сохраняет результат.
"""

import os
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

from renderer.text_layout import TextLayout
from bot.parser import DayMenu


class ImageRenderer:
    """Класс для генерации изображений меню."""
    
    def __init__(
        self,
        template_path: str,
        zones: Dict[str, Dict],
        fonts_config: Dict,
        layout_config: Dict,
        warning_config: Optional[Dict] = None
    ):
        """
        Инициализация рендерера.
        
        Args:
            template_path: Путь к фоновому шаблону
            zones: Словарь с координатами зон для каждого дня
            fonts_config: Конфигурация шрифтов (title, description)
            layout_config: Конфигурация layout (line_spacing, dish_spacing)
        """
        self.template_path = template_path
        self.zones = zones
        self.fonts_config = fonts_config
        self.layout_config = layout_config
        self.warning_config = warning_config or {}
        
        # Загружаем шрифты
        self.title_font = self._load_font(
            fonts_config['title']['file'],
            fonts_config['title']['size']
        )
        self.desc_font = self._load_font(
            fonts_config['description']['file'],
            fonts_config['description']['size']
        )
        
        # Создаем layout-менеджеры
        self.title_layout = TextLayout(
            self.title_font,
            layout_config['line_spacing']
        )
        self.desc_layout = TextLayout(
            self.desc_font,
            layout_config['line_spacing']
        )
        
        # Шрифт для warning-блока (увеличенный на multiplier)
        warning_multiplier = self.warning_config.get('font_size_multiplier', 1.2)
        warning_size = int(fonts_config['title']['size'] * warning_multiplier)
        self.warning_font = self._load_font(
            fonts_config['title']['file'],
            warning_size
        )
        
        # Шрифт для блока дат (используем обычный title)
        self.date_font = self.title_font
    
    def _load_font(self, font_path: str, size: float) -> ImageFont.FreeTypeFont:
        """
        Загружает шрифт из файла.
        
        Args:
            font_path: Путь к файлу шрифта
            size: Размер шрифта
            
        Returns:
            Загруженный шрифт
            
        Raises:
            FileNotFoundError: Если файл шрифта не найден
        """
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Шрифт не найден: {font_path}")
        
        return ImageFont.truetype(font_path, int(size))
    
    def _format_title(self, text: str) -> str:
        """
        Форматирует название блюда согласно настройкам.
        
        Args:
            text: Исходный текст
            
        Returns:
            Отформатированный текст
        """
        if self.fonts_config['title'].get('uppercase', False):
            return text.upper()
        return text
    
    def _calculate_dish_height(
        self,
        title: str,
        description: str,
        max_width: int
    ) -> int:
        """
        Рассчитывает высоту блока блюда (название + описание).
        
        Args:
            title: Название блюда
            description: Описание блюда
            max_width: Максимальная ширина зоны
            
        Returns:
            Высота блока в пикселях
        """
        formatted_title = self._format_title(title)
        title_lines = self.title_layout.wrap_text(formatted_title, max_width)
        title_height = self.title_layout.calculate_text_height(title_lines)
        
        desc_lines = self.desc_layout.wrap_text(description, max_width)
        desc_height = self.desc_layout.calculate_text_height(desc_lines)
        
        # Высота = название + отступ + описание
        total_height = title_height + self.layout_config['dish_spacing'] + desc_height
        
        return total_height
    
    def _render_day_menu(
        self,
        draw: ImageDraw.ImageDraw,
        day: str,
        dishes: List[Dict],
        zone: Dict
    ) -> bool:
        """
        Рендерит меню для одного дня.
        
        Args:
            draw: ImageDraw объект для рисования
            day: Название дня
            dishes: Список блюд для этого дня
            zone: Зона для размещения текста (x, y, width, max_height)
            
        Returns:
            True если всё поместилось, False если текст обрезан
        """
        x = zone['x']
        y = zone['y']
        width = zone['width']
        max_height = zone['max_height']
        
        current_y = y
        used_height = 0
        
        # Цвет текста (черный по умолчанию)
        text_color = (0, 0, 0)
        
        for dish in dishes:
            title = dish['title']
            description = dish['desc']
            
            # Рассчитываем высоту текущего блюда
            dish_height = self._calculate_dish_height(title, description, width)
            
            # Проверяем, помещается ли блюдо
            if used_height + dish_height > max_height:
                # Пробуем уменьшить межстрочный интервал
                # Это упрощенный подход - можно улучшить
                return False
            
            # Рисуем название блюда
            formatted_title = self._format_title(title)
            title_height = self.title_layout.draw_text_multiline(
                draw,
                formatted_title,
                (x, current_y),
                width,
                fill=text_color
            )
            
            current_y += title_height + self.layout_config['dish_spacing']
            used_height += title_height + self.layout_config['dish_spacing']
            
            # Рисуем описание
            desc_height = self.desc_layout.draw_text_multiline(
                draw,
                description,
                (x, current_y),
                width,
                fill=text_color
            )
            
            current_y += desc_height
            used_height += desc_height
        
        return True
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Конвертирует HEX цвет в RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _render_date_block(
        self,
        draw: ImageDraw.ImageDraw,
        date_range: str,
        date_config: Dict,
        zones: Dict
    ) -> None:
        """
        Рендерит блок с диапазоном дат.
        
        Args:
            draw: ImageDraw объект
            date_range: Строка с диапазоном дат (например, "15.12–19.12")
            date_config: Конфигурация блока дат
            zones: Словарь зон (для получения date_block)
        """
        if 'date_block' not in zones:
            return
        
        block = zones['date_block']
        x = block['x']
        y = block['y']
        width = block['width']
        height = block['height']
        
        # Получаем цвета из конфига
        border_color = self._hex_to_rgb(date_config.get('border_color', '#F2994A'))
        text_color = self._hex_to_rgb(date_config.get('text_color', '#000000'))
        border_radius = date_config.get('border_radius', 8)
        border_width = date_config.get('border_width', 2)
        
        # Рисуем закругленный прямоугольник с рамкой
        # Создаем маску для скругления
        from PIL import Image, ImageDraw
        
        # Рисуем прямоугольник с рамкой
        draw.rounded_rectangle(
            [(x, y), (x + width, y + height)],
            radius=border_radius,
            outline=border_color,
            width=border_width
        )
        
        # Вычисляем центр для текста
        text_bbox = draw.textbbox((0, 0), date_range, font=self.date_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2
        
        # Рисуем текст
        draw.text((text_x, text_y), date_range, font=self.date_font, fill=text_color)
    
    def _render_warning_block(
        self,
        draw: ImageDraw.ImageDraw,
        day: str,
        zone: Dict,
        warning_config: Dict,
        disabled_until: Optional[str] = None
    ) -> None:
        """
        Рендерит warning-блок для дня без бизнес-ланчей.
        
        Args:
            draw: ImageDraw объект
            day: Название дня
            zone: Зона дня
            warning_config: Конфигурация warning-блока
            disabled_until: Дата до которой не будет бизнес-ланчей
        """
        x = zone['x']
        y = zone['y']
        width = zone['width']
        max_height = zone['max_height']
        
        # Получаем цвета из конфига
        background = self._hex_to_rgb(warning_config.get('background', '#FCE4D6'))
        border_color = self._hex_to_rgb(warning_config.get('border_color', '#C0392B'))
        text_color = self._hex_to_rgb(warning_config.get('text_color', '#C0392B'))
        border_radius = warning_config.get('border_radius', 18)
        border_width = warning_config.get('border_width', 3)
        
        # Формируем текст
        if disabled_until:
            lines = [
                f"ДО {disabled_until}",
                "БИЗНЕС ЛАНЧЕЙ",
                "НЕ БУДЕТ"
            ]
        else:
            lines = [
                "БИЗНЕС ЛАНЧЕЙ",
                "НЕ БУДЕТ"
            ]
        
        # Рассчитываем размер блока текста
        total_text_height = 0
        max_text_width = 0
        line_heights = []
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=self.warning_font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            line_heights.append(line_height)
            total_text_height += line_height
            max_text_width = max(max_text_width, line_width)
        
        # Добавляем отступы между строками
        line_spacing = 8
        total_text_height += line_spacing * (len(lines) - 1)
        
        # Добавляем внутренние отступы
        padding = 20
        block_width = min(max_text_width + padding * 2, width)
        block_height = min(total_text_height + padding * 2, max_height)
        
        # Центрируем блок в зоне
        block_x = x + (width - block_width) // 2
        block_y = y + (max_height - block_height) // 2
        
        # Рисуем фон и рамку
        draw.rounded_rectangle(
            [(block_x, block_y), (block_x + block_width, block_y + block_height)],
            radius=border_radius,
            fill=background,
            outline=border_color,
            width=border_width
        )
        
        # Рисуем текст по центру
        current_y = block_y + padding
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=self.warning_font)
            line_width = bbox[2] - bbox[0]
            line_x = block_x + (block_width - line_width) // 2
            draw.text((line_x, current_y), line, font=self.warning_font, fill=text_color)
            current_y += line_heights[i] + (line_spacing if i < len(lines) - 1 else 0)
    
    def render(self, menu_data: Dict, output_path: str, date_config: Optional[Dict] = None, warning_config: Optional[Dict] = None) -> Optional[str]:
        """
        Генерирует изображение меню.
        
        Args:
            menu_data: Словарь с данными меню:
                - date_range: строка с диапазоном дат или None
                - дни недели: DayMenu объекты
            output_path: Путь для сохранения изображения
            date_config: Конфигурация блока дат (из settings.yaml)
            warning_config: Конфигурация warning-блока (из settings.yaml)
            
        Returns:
            None при успехе, сообщение об ошибке при неудаче
        """
        try:
            # Загружаем шаблон
            if not os.path.exists(self.template_path):
                return f"Шаблон не найден: {self.template_path}"
            
            img = Image.open(self.template_path).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # Рендерим блок дат, если есть
            date_range = menu_data.get('date_range')
            if date_range and date_config and 'date_block' in self.zones:
                self._render_date_block(draw, date_range, date_config, self.zones)
            
            # Рендерим меню для каждого дня
            for day in ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']:
                if day not in self.zones or day not in menu_data:
                    continue
                
                day_menu = menu_data[day]
                
                # Пропускаем дни без данных (None или пустые)
                if day_menu is None:
                    continue
                
                zone = self.zones[day]
                
                # Проверяем статус дня
                if day_menu.status == "disabled":
                    # Рендерим warning-блок
                    if warning_config:
                        self._render_warning_block(
                            draw,
                            day,
                            zone,
                            warning_config,
                            day_menu.disabled_until
                        )
                elif day_menu.status == "normal" and day_menu.dishes:
                    # Рендерим обычные блюда
                    success = self._render_day_menu(
                        draw,
                        day,
                        day_menu.dishes,
                        zone
                    )
                    if not success:
                        # В будущем можно реализовать более умное сжатие
                        pass  # Пока просто продолжаем
            
            # Создаем директорию для вывода, если её нет
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Сохраняем изображение
            img.save(output_path, 'PNG')
            
            return None  # Успех
            
        except Exception as e:
            return f"Ошибка при генерации изображения: {str(e)}"

