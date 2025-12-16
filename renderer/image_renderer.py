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
        
        # Загружаем шрифты (заголовки и описания - обычные, не жирные)
        self.title_font = self._load_font(
            fonts_config['title']['file'],
            fonts_config['title']['size'],
            bold=False  # Заголовки обычные (не жирные)
        )
        self.desc_font = self._load_font(
            fonts_config['description']['file'],
            fonts_config['description']['size'],
            bold=False  # Описания обычные
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
        
        # Шрифт для warning-блока (увеличенный на multiplier, жирный)
        warning_multiplier = self.warning_config.get('font_size_multiplier', 1.2)
        warning_size = int(fonts_config['title']['size'] * warning_multiplier)
        self.warning_font = self._load_font(
            fonts_config['title']['file'],
            warning_size,
            bold=True  # Warning текст тоже жирный
        )
        
        # Шрифт для блока дат (жирный вариант, увеличенный размер)
        date_size = int(fonts_config['title']['size'] * 1.3)  # Увеличиваем на 30%
        self.date_font = self._load_font(
            fonts_config['title']['file'],
            date_size,
            bold=True  # Дата жирная
        )
    
    def _load_font(self, font_path: str, size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
        """
        Загружает шрифт из файла.
        
        Args:
            font_path: Путь к файлу шрифта
            size: Размер шрифта
            bold: Использовать жирный вариант (если доступен)
            
        Returns:
            Загруженный шрифт
            
        Raises:
            FileNotFoundError: Если файл шрифта не найден
        """
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Шрифт не найден: {font_path}")
        
        # Пытаемся загрузить жирный вариант через индекс (обычно index 1 = Bold)
        if bold:
            try:
                return ImageFont.truetype(font_path, int(size), index=1)
            except (OSError, IndexError):
                # Если жирный вариант недоступен, используем обычный
                pass
        
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
    
    def _calculate_optimal_font_sizes(
        self,
        dishes: List[Dict],
        width: int,
        max_height: int
    ) -> tuple:
        """
        Рассчитывает МАКСИМАЛЬНЫЕ размеры шрифтов для всех блюд, чтобы они заполнили зону.
        Учитывает отступ в 5px от краев рамки.
        Текст автоматически увеличивается до максимально возможного размера.
        
        Returns:
            (title_font_size, desc_font_size, actual_title_layout, actual_desc_layout)
        """
        base_title_size = self.fonts_config['title']['size']
        base_desc_size = self.fonts_config['description']['size']
        line_spacing = self.layout_config['line_spacing']
        # Константа: отступ между названием блюда и его описанием всегда 1 пиксель
        TITLE_TO_DESC_SPACING = 1
        between_dishes_spacing = self.layout_config.get('between_dishes_spacing', 10)
        
        # Отступы от краев рамки (2px со всех сторон для большего пространства под текст)
        padding = 2
        available_width = width - (padding * 2)  # Отступы слева и справа
        available_height = max_height - (padding * 2)  # Отступы сверху и снизу
        
        # Минимальный и максимальный размеры шрифта
        min_size = 8  # Уменьшаем минимум, чтобы гарантировать, что текст поместится
        max_size = int(base_title_size * 4.0)  # Увеличиваем максимальный размер для автоувеличения
        
        best_title_size = min_size
        best_desc_size = int(min_size * (base_desc_size / base_title_size))
        
        # КРИТИЧЕСКИ ВАЖНО: ищем максимальный размер, при котором ВСЕ блюда гарантированно поместятся
        # Идем от максимального к минимальному, чтобы найти самый большой размер, который поместится
        # Это гарантирует, что все блюда будут видны
        for title_size in range(max_size, min_size - 1, -1):  # Идем сверху вниз
            desc_size = int(title_size * (base_desc_size / base_title_size))
            if desc_size < 8:  # Минимальный размер для описания
                desc_size = 8
            
            # Создаем временные шрифты для тестирования (заголовки - обычные)
            temp_title_font = self._load_font(self.fonts_config['title']['file'], title_size, bold=False)
            temp_desc_font = self._load_font(self.fonts_config['description']['file'], desc_size, bold=False)
            temp_title_layout = TextLayout(temp_title_font, line_spacing)
            temp_desc_layout = TextLayout(temp_desc_font, line_spacing)
            
            # Проверяем, помещаются ли ВСЕ блюда с текущим размером
            total_height = 0
            all_fit = True
            
            for idx, dish in enumerate(dishes):
                title = dish['title']
                description = dish['desc']
                formatted_title = self._format_title(title)
                
                # Используем доступную ширину (с учетом отступов)
                title_lines = temp_title_layout.wrap_text(formatted_title, available_width)
                title_height = temp_title_layout.calculate_text_height(title_lines)
                
                desc_lines = temp_desc_layout.wrap_text(description, available_width)
                desc_height = temp_desc_layout.calculate_text_height(desc_lines)
                
                # Для последнего блюда не добавляем between_dishes_spacing
                extra_spacing = between_dishes_spacing if idx < len(dishes) - 1 else 0
                dish_height = title_height + TITLE_TO_DESC_SPACING + desc_height + extra_spacing
                
                # СТРОГАЯ ПРОВЕРКА: общая высота должна быть строго меньше или равна available_height
                # Добавляем запас (5px) для безопасности из-за возможных расхождений между расчетом и реальным рендерингом
                safety_margin = 5
                if total_height + dish_height > available_height - safety_margin:
                    all_fit = False
                    break
                
                total_height += dish_height
            
            # Если все блюда поместились, используем этот размер (он максимальный из подходящих)
            if all_fit and total_height > 0:
                best_title_size = title_size
                best_desc_size = desc_size
                break  # Нашли максимальный подходящий размер, останавливаемся
        
        # ФИНАЛЬНАЯ ПРОВЕРКА: убеждаемся, что найденный размер действительно помещает все блюда
        # Создаем финальные layout'ы для проверки
        optimal_title_font = self._load_font(self.fonts_config['title']['file'], best_title_size, bold=False)
        optimal_desc_font = self._load_font(self.fonts_config['description']['file'], best_desc_size, bold=False)
        optimal_title_layout = TextLayout(optimal_title_font, line_spacing)
        optimal_desc_layout = TextLayout(optimal_desc_font, line_spacing)
        
        # Проверяем еще раз, что все помещается с финальным размером
        final_total_height = 0
        for idx, dish in enumerate(dishes):
            title = dish['title']
            description = dish['desc']
            formatted_title = self._format_title(title)
            
            title_lines = optimal_title_layout.wrap_text(formatted_title, available_width)
            title_height = optimal_title_layout.calculate_text_height(title_lines)
            
            desc_lines = optimal_desc_layout.wrap_text(description, available_width)
            desc_height = optimal_desc_layout.calculate_text_height(desc_lines)
            
            extra_spacing = between_dishes_spacing if idx < len(dishes) - 1 else 0
            dish_height = title_height + TITLE_TO_DESC_SPACING + desc_height + extra_spacing
            final_total_height += dish_height
        
        # КРИТИЧЕСКАЯ ПРОВЕРКА: Если финальная высота превышает доступную, итеративно уменьшаем размер
        # Это гарантирует, что все точно поместится с запасом безопасности
        safety_margin = 5
        max_iterations = 10  # Максимальное количество итераций для предотвращения бесконечного цикла
        
        for iteration in range(max_iterations):
            if final_total_height <= available_height - safety_margin:
                break  # Все помещается с запасом
            
            # Уменьшаем размер пропорционально с запасом
            scale_factor = (available_height - safety_margin) / final_total_height
            best_title_size = max(min_size, int(best_title_size * scale_factor * 0.95))  # Дополнительный коэффициент для гарантии
            best_desc_size = max(8, int(best_desc_size * scale_factor * 0.95))
            
            # Пересоздаем layout'ы с уменьшенным размером
            optimal_title_font = self._load_font(self.fonts_config['title']['file'], best_title_size, bold=False)
            optimal_desc_font = self._load_font(self.fonts_config['description']['file'], best_desc_size, bold=False)
            optimal_title_layout = TextLayout(optimal_title_font, line_spacing)
            optimal_desc_layout = TextLayout(optimal_desc_font, line_spacing)
            
            # Пересчитываем финальную высоту с новым размером
            final_total_height = 0
            for idx, dish in enumerate(dishes):
                title = dish['title']
                description = dish['desc']
                formatted_title = self._format_title(title)
                
                title_lines = optimal_title_layout.wrap_text(formatted_title, available_width)
                title_height = optimal_title_layout.calculate_text_height(title_lines)
                
                desc_lines = optimal_desc_layout.wrap_text(description, available_width)
                desc_height = optimal_desc_layout.calculate_text_height(desc_lines)
                
                extra_spacing = between_dishes_spacing if idx < len(dishes) - 1 else 0
                dish_height = title_height + TITLE_TO_DESC_SPACING + desc_height + extra_spacing
                final_total_height += dish_height
        
        return best_title_size, best_desc_size, optimal_title_layout, optimal_desc_layout
    
    def _render_day_menu(
        self,
        draw: ImageDraw.ImageDraw,
        day: str,
        dishes: List[Dict],
        zone: Dict
    ) -> bool:
        """
        Рендерит меню для одного дня с динамическим масштабированием текста.
        
        Args:
            draw: ImageDraw объект для рисования
            day: Название дня
            dishes: Список блюд для этого дня
            zone: Зона для размещения текста (x, y, width, max_height)
            
        Returns:
            True если хотя бы одно блюдо отрисовано
        """
        x = zone['x']
        y = zone['y']
        width = zone['width']
        max_height = zone['max_height']
        
        if not dishes:
            return False
        
        # Отступы от краев рамки (2px со всех сторон для большего пространства под текст)
        padding = 2
        available_width = width - (padding * 2)
        available_height = max_height - (padding * 2)
        
        # Рассчитываем оптимальные размеры шрифтов (с учетом отступов)
        title_size, desc_size, title_layout, desc_layout = self._calculate_optimal_font_sizes(
            dishes, width, max_height
        )
        
        # Начальные координаты с учетом отступа
        start_x = x + padding
        start_y = y + padding
        current_y = start_y
        used_height = 0
        # Константа: отступ между названием блюда и его описанием всегда 1 пиксель
        TITLE_TO_DESC_SPACING = 1
        
        # Цвета текста: названия блюд и описания
        title_color = self._hex_to_rgb('#695245')  # Коричневый для названий
        desc_color = self._hex_to_rgb('#5a4438')  # Тёмно-коричневый для описаний (темнее для лучшей читаемости)
        between_dishes_spacing = self.layout_config.get('between_dishes_spacing', 10)
        
        for idx, dish in enumerate(dishes):
            is_last_dish = (idx == len(dishes) - 1)
            title = dish['title']
            description = dish['desc']
            formatted_title = self._format_title(title)
            
            # Рассчитываем высоту текущего блюда (используем доступную ширину с отступами)
            title_lines = title_layout.wrap_text(formatted_title, available_width)
            title_height = title_layout.calculate_text_height(title_lines)
            
            desc_lines = desc_layout.wrap_text(description, available_width)
            desc_height = desc_layout.calculate_text_height(desc_lines)
            
            # Для расчета используем между блюдами отступ (кроме последнего)
            extra_spacing = between_dishes_spacing if not is_last_dish else 0
            dish_height = title_height + TITLE_TO_DESC_SPACING + desc_height + extra_spacing
            
            # Проверяем, помещается ли блюдо
            # Но не останавливаемся - продолжаем рендерить все блюда
            # (оптимальный размер уже рассчитан так, чтобы все поместились)
            
            # Сохраняем начальную Y-координату для названия (для точного расчета отступа)
            title_start_y = current_y
            
            # Вычисляем строки названия для точного расчета нижней границы
            title_lines = title_layout.wrap_text(formatted_title, available_width)
            
            # Рисуем название блюда (с учетом отступа слева, с letter spacing и легкой обводкой для жирности)
            title_height_actual = title_layout.draw_text_multiline(
                draw,
                formatted_title,
                (start_x, current_y),
                available_width,
                fill=title_color,
                stroke_width=1,  # Легкая обводка для эффекта жирности
                stroke_fill=title_color,
                letter_spacing=1  # 1 пиксель между буквами
            )
            
            # КРИТИЧЕСКИ ВАЖНО: вычисляем точную нижнюю границу названия
            # Вычисляем Y-координату и нижнюю границу последней строки названия
            if title_lines:
                # Находим Y-координату последней строки, проходясь по всем предыдущим строкам
                last_line_y = title_start_y
                for line in title_lines[:-1]:
                    bbox = draw.textbbox((start_x, last_line_y), line, font=title_layout.font)
                    line_height = bbox[3] - bbox[1]
                    last_line_y += line_height + title_layout.line_spacing
                
                # Получаем точную нижнюю границу последней строки названия
                last_line_bbox = draw.textbbox((start_x, last_line_y), title_lines[-1], font=title_layout.font)
                title_bottom_y = last_line_bbox[3]  # Нижняя координата названия (bbox[3] = bottom)
            else:
                # Если нет строк (не должно быть, но на всякий случай)
                title_bottom_y = title_start_y + title_height_actual
            
            # Устанавливаем позицию для описания: ровно 1 пиксель ниже нижней границы названия
            # ВАЖНО: это гарантирует стабильный отступ в 1 пиксель независимо от масштабирования, размера шрифта и количества строк
            current_y = title_bottom_y + TITLE_TO_DESC_SPACING
            
            # Обновляем used_height для отслеживания использованного пространства
            used_height += (current_y - title_start_y)
            
            # ВАЖНО: Проверяем, не вышли ли за границы после названия
            # Если вышли, это означает ошибку в расчете - все должно помещаться
            # Но для надежности проверяем и пропускаем блюдо, если оно не помещается
            safety_margin = 3  # Запас для безопасности
            if current_y > start_y + available_height - safety_margin:
                # Это не должно происходить, если расчет правильный, но на всякий случай пропускаем
                continue
            
            # Рисуем описание (с учетом отступа слева)
            desc_height_actual = desc_layout.draw_text_multiline(
                draw,
                description,
                (start_x, current_y),
                available_width,
                fill=desc_color
            )
            
            current_y += desc_height_actual
            used_height += desc_height_actual
            
            # Добавляем отступ между блюдами (между описанием текущего и названием следующего)
            # НЕ добавляем отступ после последнего блюда
            if not is_last_dish:
                current_y += between_dishes_spacing
                used_height += between_dishes_spacing
            
            # ВАЖНО: Проверяем, не вышли ли за границы после описания
            # Если вышли, следующее блюдо не поместится - пропускаем его
            safety_margin = 3  # Запас для безопасности
            if current_y > start_y + available_height - safety_margin:
                # Это не должно происходить, если расчет правильный, но на всякий случай останавливаемся
                break
        
        # Возвращаем True если хотя бы одно блюдо отрисовано
        return used_height > 0
    
    def _draw_zone_border(
        self,
        draw: ImageDraw.ImageDraw,
        zone: Dict,
        day: str
    ) -> None:
        """
        Рисует видимую рамку вокруг зоны для отладки.
        
        Args:
            draw: ImageDraw объект
            zone: Зона с координатами (x, y, width, max_height)
            day: Название дня для отображения
        """
        try:
            x = zone['x']
            y = zone['y']
            width = zone['width']
            max_height = zone['max_height']
            
            # Рисуем красную рамку (4 отдельные линии для надежности)
            border_color = (255, 0, 0)  # Красный цвет для видимости
            border_width = 8  # Очень толстая линия для видимости
            
            # Проверяем, что координаты в пределах изображения
            # (временная проверка, потом можно убрать)
            
            # Верхняя линия
            draw.rectangle(
                [(x, y), (x + width, y + border_width)],
                fill=border_color
            )
            # Нижняя линия
            draw.rectangle(
                [(x, y + max_height - border_width), (x + width, y + max_height)],
                fill=border_color
            )
            # Левая линия
            draw.rectangle(
                [(x, y), (x + border_width, y + max_height)],
                fill=border_color
            )
            # Правая линия
            draw.rectangle(
                [(x + width - border_width, y), (x + width, y + max_height)],
                fill=border_color
            )
            
            # Рисуем большой желтый фон для метки дня
            label_text = f"{day}"
            try:
                label_font = ImageFont.load_default()
            except:
                label_font = None
            
            # Большой желтый прямоугольник для метки
            label_size = 40
            draw.rectangle(
                [(x + 5, y + 5), (x + 5 + label_size, y + 5 + label_size)],
                fill=(255, 255, 0)  # Желтый
            )
            
            # Текст метки (большой и черный)
            if label_font:
                try:
                    draw.text((x + 10, y + 10), label_text, fill=(0, 0, 0), font=label_font)
                except:
                    pass
        except Exception as e:
            # В случае ошибки хотя бы попробуем нарисовать тестовый квадрат
            try:
                draw.rectangle([(10, 10), (50, 50)], fill=(255, 0, 0))
            except:
                pass
    
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
        
        # Получаем цвета из конфига (текст дат - оранжевый #e9954d)
        border_color = self._hex_to_rgb(date_config.get('border_color', '#F2994A'))
        text_color = self._hex_to_rgb('#e9954d')  # Оранжевый цвет для дат
        border_radius = date_config.get('border_radius', 8)
        border_width = 1  # Тонкая обводка (1px вместо стандартных 2px)
        
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
        
        # Вычисляем центр для текста (точное центрирование)
        # Используем anchor='mm' (middle-middle) для идеального центрирования
        center_x = x + width // 2
        center_y = y + height // 2
        
        # Рисуем текст с обводкой для дополнительной жирности, точно по центру
        draw.text(
            (center_x, center_y),
            date_range,
            font=self.date_font,
            fill=text_color,
            stroke_width=1,  # Легкая обводка для жирности
            stroke_fill=text_color,
            anchor='mm'  # Точное центрирование по горизонтали и вертикали
        )
    
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
    
    def render(self, menu_data: Dict, output_path: str, date_config: Optional[Dict] = None, warning_config: Optional[Dict] = None, show_debug_borders: bool = False) -> Optional[str]:
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
            
            # Рисуем видимые рамки зон для отладки ПОСЛЕ всего текста (поверх)
            # Только если включено в настройках (для разработки/отладки)
            if show_debug_borders:
                for day in ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']:
                    if day in self.zones:
                        self._draw_zone_border(draw, self.zones[day], day)
            
            # Создаем директорию для вывода, если её нет
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Сохраняем изображение
            img.save(output_path, 'PNG')
            
            return None  # Успех
            
        except Exception as e:
            return f"Ошибка при генерации изображения: {str(e)}"

