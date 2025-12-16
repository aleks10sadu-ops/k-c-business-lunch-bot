# Инструкция по конвертации PDF в PNG

## Требования

Для корректной работы бота необходимо конвертировать PDF-шаблон в PNG с правильными параметрами.

## Параметры конвертации

- **Размер:** 797 × 1132 пикселей (вертикальная ориентация)
- **Формат:** PNG с альфа-каналом (если нужна прозрачность) или без
- **Примечание:** Разрешение зависит от исходного PDF и нужного размера

## Способы конвертации

### 1. Adobe Acrobat / Adobe Acrobat Reader

1. Откройте PDF файл
2. Файл → Экспорт → Изображение → PNG
3. Настройки:
   - Размер: 797 × 1132 пикселей
   - Или используйте разрешение, которое даст нужный размер
4. Сохраните как `assets/template.png`

### 2. Inkscape (бесплатно)

```bash
inkscape --export-type=png --export-width=797 --export-height=1132 --export-filename=assets/template.png input.pdf
```

Или через GUI:
1. Откройте PDF в Inkscape
2. Файл → Экспортировать растровое изображение
3. Установите размер: 797 × 1132 px

### 3. ImageMagick (командная строка)

```bash
convert -resize 797x1132! input.pdf assets/template.png
```

**Примечание:** `!` означает точный размер без сохранения пропорций

### 4. Онлайн-конвертеры

Используйте любой онлайн-конвертер PDF → PNG:
- [CloudConvert](https://cloudconvert.com/pdf-to-png)
- [Zamzar](https://www.zamzar.com/convert/pdf-to-png/)
- [ILovePDF](https://www.ilovepdf.com/pdf_to_png)

**Важно:** После конвертации проверьте, что размер изображения точно **420 × 595 пикселей**.

### 5. Python скрипт (если установлен pdf2image)

```bash
pip install pdf2image pillow
```

```python
from pdf2image import convert_from_path
from PIL import Image

# Конвертация с разрешением 72 DPI
images = convert_from_path('input.pdf', dpi=72)

if images:
    img = images[0]
    # Убеждаемся, что размер правильный
    if img.size != (797, 1132):
        img = img.resize((797, 1132), Image.Resampling.LANCZOS)
    img.save('assets/template.png', 'PNG')
```

## Проверка результата

После конвертации проверьте размер файла:

**Windows (PowerShell):**
```powershell
Get-Item assets/template.png | Select-Object Name, @{Name="Size";Expression={"{0}x{1}" -f $_.Width, $_.Height}}
```

**Linux/Mac:**
```bash
identify assets/template.png
# или
file assets/template.png
```

**Python:**
```python
from PIL import Image
img = Image.open('assets/template.png')
print(f"Size: {img.size}")  # Должно быть (797, 1132)
```

## Устранение проблем

**Размер не совпадает:**
- Проверьте ориентацию страницы (должна быть вертикальная)
- Если размер отличается, используйте `resize` для приведения к 797 × 1132 пикселей
- При изменении размера координаты в `zones.yaml` нужно пересчитать пропорционально

