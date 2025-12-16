"""
Модуль для работы с текстовым layout.

Осуществляет перенос строк, расчет высоты текста
и размещение текста в заданных зонах.
"""

from typing import List, Tuple
from PIL import Image, ImageDraw, ImageFont


class TextLayout:
    """Класс для работы с текстовым layout и переносами строк."""
    
    def __init__(self, font: ImageFont.FreeTypeFont, line_spacing: int):
        """
        Инициализация layout-менеджера.
        
        Args:
            font: Шрифт для измерения текста
            line_spacing: Межстрочный интервал в пикселях
        """
        self.font = font
        self.line_spacing = line_spacing
    
    def wrap_text(self, text: str, max_width: int) -> List[str]:
        """
        Разбивает текст на строки, учитывая максимальную ширину.
        
        Args:
            text: Текст для разбиения
            max_width: Максимальная ширина в пикселях
            
        Returns:
            Список строк, каждая из которых помещается в max_width
        """
        if not text:
            return []
        
        # Создаем временный Draw объект для измерения
        temp_img = Image.new('RGB', (100, 100))
        temp_draw = ImageDraw.Draw(temp_img)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Пробуем добавить слово к текущей строке
            test_line = ' '.join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=self.font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                # Текущая строка заполнена, начинаем новую
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Даже одно слово не помещается - добавляем как есть
                    lines.append(word)
        
        # Добавляем последнюю строку
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def calculate_text_height(self, text_lines: List[str]) -> int:
        """
        Рассчитывает высоту блока текста.
        
        Args:
            text_lines: Список строк текста
            
        Returns:
            Высота блока в пикселях
        """
        if not text_lines:
            return 0
        
        # Создаем временный Draw объект для измерения
        temp_img = Image.new('RGB', (100, 100))
        temp_draw = ImageDraw.Draw(temp_img)
        
        total_height = 0
        
        for i, line in enumerate(text_lines):
            bbox = temp_draw.textbbox((0, 0), line, font=self.font)
            line_height = bbox[3] - bbox[1]
            
            if i > 0:
                total_height += self.line_spacing
            
            total_height += line_height
        
        return total_height
    
    def draw_text_multiline(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        max_width: int,
        fill: Tuple[int, int, int] = (0, 0, 0),
        stroke_width: int = 0,
        stroke_fill: Tuple[int, int, int] = (0, 0, 0),
        letter_spacing: int = 0
    ) -> int:
        """
        Рисует многострочный текст с автоматическим переносом.
        
        Args:
            draw: ImageDraw объект для рисования
            text: Текст для отрисовки
            position: Начальная позиция (x, y)
            max_width: Максимальная ширина в пикселях
            fill: Цвет текста (RGB)
            stroke_width: Толщина обводки (0 = без обводки)
            stroke_fill: Цвет обводки (RGB)
            letter_spacing: Отступ между буквами в пикселях (0 = без отступа)
            
        Returns:
            Высота нарисованного текста
        """
        lines = self.wrap_text(text, max_width)
        
        x, y = position
        current_y = y
        
        for i, line in enumerate(lines):
            if letter_spacing > 0:
                # Рисуем каждую букву отдельно с отступом
                current_x = x
                for char in line:
                    if char == ' ':
                        # Для пробелов используем обычную ширину
                        bbox = draw.textbbox((current_x, current_y), ' ', font=self.font)
                        current_x = bbox[2]
                    else:
                        # Рисуем букву с обводкой (если указана)
                        draw.text(
                            (current_x, current_y),
                            char,
                            font=self.font,
                            fill=fill,
                            stroke_width=int(stroke_width) if stroke_width > 0 else 0,
                            stroke_fill=stroke_fill if stroke_width > 0 else None
                        )
                        # Получаем ширину буквы и добавляем отступ
                        bbox = draw.textbbox((current_x, current_y), char, font=self.font)
                        char_width = bbox[2] - bbox[0]
                        current_x += char_width + letter_spacing
            else:
                # Рисуем текст обычным способом (без letter spacing)
                draw.text(
                    (x, current_y),
                    line,
                    font=self.font,
                    fill=fill,
                    stroke_width=stroke_width if stroke_width > 0 else 0,
                    stroke_fill=stroke_fill if stroke_width > 0 else None
                )
            
            # Рассчитываем высоту текущей строки
            bbox = draw.textbbox((x, current_y), line, font=self.font)
            line_height = bbox[3] - bbox[1]
            
            # Всегда добавляем line_spacing после строки (кроме последней)
            # Это гарантирует минимальный отступ 5px между строками
            if i < len(lines) - 1:
                current_y += line_height + self.line_spacing
            else:
                current_y += line_height
        
        return current_y - y

