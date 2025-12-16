"""
Веб-интерфейс для визуального редактирования зон меню.
Запускается локально на http://localhost:5000
"""

import os
import json
from flask import Flask, render_template_string, request, jsonify, send_from_directory
import yaml

app = Flask(__name__)
ZONES_FILE = 'config/zones.yaml'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Редактор зон меню</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            margin-top: 0;
            color: #333;
        }
        .canvas-container {
            position: relative;
            border: 2px solid #ddd;
            display: inline-block;
            background: white;
        }
        #templateCanvas {
            display: block;
            cursor: crosshair;
        }
        .zone {
            position: absolute;
            border: 3px solid #ff0000;
            background: rgba(255, 0, 0, 0.1);
            cursor: move;
        }
        .zone-label {
            position: absolute;
            top: 5px;
            left: 5px;
            background: rgba(255, 255, 0, 0.9);
            padding: 2px 8px;
            font-weight: bold;
            font-size: 14px;
            border-radius: 3px;
        }
        .controls {
            margin-top: 20px;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover {
            background: #45a049;
        }
        button.danger {
            background: #f44336;
        }
        button.danger:hover {
            background: #da190b;
        }
        .info {
            margin-top: 10px;
            padding: 10px;
            background: #e3f2fd;
            border-radius: 4px;
            color: #1976d2;
        }
        .zone-list {
            margin-top: 20px;
        }
        .zone-item {
            padding: 10px;
            margin: 5px 0;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .zone-item.active {
            border-color: #4CAF50;
            background: #f1f8f4;
        }
        input[type="number"] {
            width: 80px;
            padding: 5px;
            margin: 0 5px;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Редактор зон меню</h1>
        
        <div class="canvas-container" id="canvasContainer">
            <canvas id="templateCanvas"></canvas>
            <div id="zones"></div>
        </div>
        
        <div class="controls">
            <button onclick="saveZones()">💾 Сохранить координаты</button>
            <button onclick="resetZones()">🔄 Сбросить изменения</button>
            <button onclick="reloadZones()">🔄 Перезагрузить из файла</button>
            <button class="danger" onclick="deleteSelectedZone()">🗑 Удалить выбранную зону</button>
            
            <div class="info" id="info">
                Выберите зону, чтобы редактировать её координаты ниже. Или перетащите зону мышью.
            </div>
        </div>
        
        <div class="zone-list">
            <h3>Зоны:</h3>
            <div id="zoneEditor">
                <!-- Зоны будут здесь -->
            </div>
        </div>
    </div>

    <script>
        let canvas, ctx;
        let zones = {};
        let selectedZone = null;
        let isDragging = false;
        let dragOffset = {x: 0, y: 0};
        let image = new Image();
        
        // Дни недели
        const days = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ'];
        // Специальные зоны
        const specialZones = ['date_block'];
        
        // Загрузка изображения шаблона
        image.onload = function() {
            canvas = document.getElementById('templateCanvas');
            ctx = canvas.getContext('2d');
            canvas.width = image.width;
            canvas.height = image.height;
            ctx.drawImage(image, 0, 0);
            
            // Загружаем зоны
            loadZones();
        };
        
        image.src = '/assets/template.png';
        
        // Загрузка зон с сервера
        async function loadZones() {
            try {
                const response = await fetch('/api/zones');
                zones = await response.json();
                renderZones();
            } catch (error) {
                console.error('Ошибка загрузки зон:', error);
            }
        }
        
        // Отображение зон
        function renderZones() {
            const zonesContainer = document.getElementById('zones');
            const editorContainer = document.getElementById('zoneEditor');
            zonesContainer.innerHTML = '';
            editorContainer.innerHTML = '';
            
            const container = document.getElementById('canvasContainer');
            
            // Рендерим зоны дней недели
            for (const day of days) {
                if (zones[day]) {
                    const zone = zones[day];
                    const div = document.createElement('div');
                    div.className = 'zone' + (selectedZone === day ? ' active' : '');
                    div.id = 'zone-' + day;
                    div.style.left = Math.round(zone.x) + 'px';
                    div.style.top = Math.round(zone.y) + 'px';
                    div.style.width = Math.round(zone.width) + 'px';
                    div.style.height = Math.round(zone.max_height) + 'px';
                    
                    const label = document.createElement('div');
                    label.className = 'zone-label';
                    label.textContent = day;
                    
                    div.appendChild(label);
                    
                    // Создаем ручки для изменения размера (8 точек)
                    const handles = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
                    handles.forEach(handle => {
                        const handleDiv = document.createElement('div');
                        handleDiv.className = 'resize-handle resize-' + handle;
                        handleDiv.style.cssText = `
                            position: absolute;
                            background: #4CAF50;
                            border: 2px solid white;
                            width: 10px;
                            height: 10px;
                            border-radius: 50%;
                            cursor: ${handle === 'nw' || handle === 'se' ? 'nwse-resize' : 
                                     handle === 'ne' || handle === 'sw' ? 'nesw-resize' :
                                     handle === 'n' || handle === 's' ? 'ns-resize' : 'ew-resize'};
                            z-index: 10;
                        `;
                        
                        // Позиционирование ручек
                        if (handle === 'nw') {
                            handleDiv.style.left = '-5px';
                            handleDiv.style.top = '-5px';
                        } else if (handle === 'n') {
                            handleDiv.style.left = '50%';
                            handleDiv.style.top = '-5px';
                            handleDiv.style.transform = 'translateX(-50%)';
                        } else if (handle === 'ne') {
                            handleDiv.style.right = '-5px';
                            handleDiv.style.top = '-5px';
                        } else if (handle === 'e') {
                            handleDiv.style.right = '-5px';
                            handleDiv.style.top = '50%';
                            handleDiv.style.transform = 'translateY(-50%)';
                        } else if (handle === 'se') {
                            handleDiv.style.right = '-5px';
                            handleDiv.style.bottom = '-5px';
                        } else if (handle === 's') {
                            handleDiv.style.left = '50%';
                            handleDiv.style.bottom = '-5px';
                            handleDiv.style.transform = 'translateX(-50%)';
                        } else if (handle === 'sw') {
                            handleDiv.style.left = '-5px';
                            handleDiv.style.bottom = '-5px';
                        } else if (handle === 'w') {
                            handleDiv.style.left = '-5px';
                            handleDiv.style.top = '50%';
                            handleDiv.style.transform = 'translateY(-50%)';
                        }
                        
                        handleDiv.addEventListener('mousedown', (e) => {
                            e.stopPropagation();
                            selectZone(day);
                            isDragging = true;
                            resizeHandle = handle;
                            const rect = canvas.getBoundingClientRect();
                            dragOffset.x = e.clientX - rect.left - zone.x;
                            dragOffset.y = e.clientY - rect.top - zone.y;
                        });
                        
                        div.appendChild(handleDiv);
                    });
                    
                    zonesContainer.appendChild(div);
                    
                    // События для перетаскивания
                    div.addEventListener('mousedown', (e) => {
                        // Игнорируем клики на ручки изменения размера
                        if (e.target.classList.contains('resize-handle')) {
                            return;
                        }
                        selectZone(day);
                        isDragging = true;
                        resizeHandle = null;
                        const rect = canvas.getBoundingClientRect();
                        const mouseX = e.clientX - rect.left;
                        const mouseY = e.clientY - rect.top;
                        // Правильный расчет offset: позиция мыши минус позиция зоны
                        dragOffset.x = mouseX - zone.x;
                        dragOffset.y = mouseY - zone.y;
                        e.preventDefault();
                    });
                    
                    // Редактор координат
                    const editor = document.createElement('div');
                    editor.className = 'zone-item' + (selectedZone === day ? ' active' : '');
                    editor.innerHTML = `
                            <strong>${day}</strong>
                        <div>
                            X: <input type="number" id="x-${day}" value="${Math.round(zone.x)}" onchange="updateZone('${day}', 'x', this.value)">
                            Y: <input type="number" id="y-${day}" value="${Math.round(zone.y)}" onchange="updateZone('${day}', 'y', this.value)">
                            Ширина: <input type="number" id="width-${day}" value="${Math.round(zone.width)}" onchange="updateZone('${day}', 'width', this.value)">
                            Высота: <input type="number" id="height-${day}" value="${Math.round(zone.max_height)}" onchange="updateZone('${day}', 'max_height', this.value)">
                            <button onclick="selectZone('${day}')">Выбрать</button>
                        </div>
                    `;
                    editorContainer.appendChild(editor);
                }
            }
            
            // Рендерим специальные зоны (date_block)
            for (const zoneName of specialZones) {
                if (zones[zoneName]) {
                    const zone = zones[zoneName];
                    const div = document.createElement('div');
                    div.className = 'zone' + (selectedZone === zoneName ? ' active' : '');
                    div.id = 'zone-' + zoneName;
                    div.style.left = Math.round(zone.x) + 'px';
                    div.style.top = Math.round(zone.y) + 'px';
                    div.style.width = Math.round(zone.width) + 'px';
                    div.style.height = Math.round(zone.height || zone.max_height || 40) + 'px';
                    div.style.borderColor = '#FF9800'; // Оранжевый для date_block
                    
                    const label = document.createElement('div');
                    label.className = 'zone-label';
                    label.textContent = zoneName === 'date_block' ? 'Даты' : zoneName;
                    
                    div.appendChild(label);
                    
                    // Создаем ручки для изменения размера
                    const handles = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];
                    handles.forEach(handle => {
                        const handleDiv = document.createElement('div');
                        handleDiv.className = 'resize-handle resize-' + handle;
                        handleDiv.style.cssText = `
                            position: absolute;
                            background: #FF9800;
                            border: 2px solid white;
                            width: 10px;
                            height: 10px;
                            border-radius: 50%;
                            cursor: ${handle === 'nw' || handle === 'se' ? 'nwse-resize' : 
                                     handle === 'ne' || handle === 'sw' ? 'nesw-resize' :
                                     handle === 'n' || handle === 's' ? 'ns-resize' : 'ew-resize'};
                            z-index: 10;
                        `;
                        
                        // Позиционирование ручек (то же самое что и для дней)
                        if (handle === 'nw') {
                            handleDiv.style.left = '-5px';
                            handleDiv.style.top = '-5px';
                        } else if (handle === 'n') {
                            handleDiv.style.left = '50%';
                            handleDiv.style.top = '-5px';
                            handleDiv.style.transform = 'translateX(-50%)';
                        } else if (handle === 'ne') {
                            handleDiv.style.right = '-5px';
                            handleDiv.style.top = '-5px';
                        } else if (handle === 'e') {
                            handleDiv.style.right = '-5px';
                            handleDiv.style.top = '50%';
                            handleDiv.style.transform = 'translateY(-50%)';
                        } else if (handle === 'se') {
                            handleDiv.style.right = '-5px';
                            handleDiv.style.bottom = '-5px';
                        } else if (handle === 's') {
                            handleDiv.style.left = '50%';
                            handleDiv.style.bottom = '-5px';
                            handleDiv.style.transform = 'translateX(-50%)';
                        } else if (handle === 'sw') {
                            handleDiv.style.left = '-5px';
                            handleDiv.style.bottom = '-5px';
                        } else if (handle === 'w') {
                            handleDiv.style.left = '-5px';
                            handleDiv.style.top = '50%';
                            handleDiv.style.transform = 'translateY(-50%)';
                        }
                        
                        handleDiv.addEventListener('mousedown', (e) => {
                            e.stopPropagation();
                            selectZone(zoneName);
                            isDragging = true;
                            resizeHandle = handle;
                            const rect = canvas.getBoundingClientRect();
                            dragOffset.x = e.clientX - rect.left - zone.x;
                            dragOffset.y = e.clientY - rect.top - zone.y;
                        });
                        
                        div.appendChild(handleDiv);
                    });
                    
                    zonesContainer.appendChild(div);
                    
                    // События для перетаскивания
                    div.addEventListener('mousedown', (e) => {
                        if (e.target.classList.contains('resize-handle')) {
                            return;
                        }
                        selectZone(zoneName);
                        isDragging = true;
                        resizeHandle = null;
                        const rect = canvas.getBoundingClientRect();
                        const mouseX = e.clientX - rect.left;
                        const mouseY = e.clientY - rect.top;
                        dragOffset.x = mouseX - zone.x;
                        dragOffset.y = mouseY - zone.y;
                        e.preventDefault();
                    });
                    
                    // Редактор координат
                    const editor = document.createElement('div');
                    editor.className = 'zone-item' + (selectedZone === zoneName ? ' active' : '');
                    const zoneHeight = zone.height || zone.max_height || 40;
                    editor.innerHTML = `
                            <strong>${zoneName === 'date_block' ? 'Блок дат' : zoneName}</strong>
                        <div>
                            X: <input type="number" id="x-${zoneName}" value="${Math.round(zone.x)}" onchange="updateZone('${zoneName}', 'x', this.value)">
                            Y: <input type="number" id="y-${zoneName}" value="${Math.round(zone.y)}" onchange="updateZone('${zoneName}', 'y', this.value)">
                            Ширина: <input type="number" id="width-${zoneName}" value="${Math.round(zone.width)}" onchange="updateZone('${zoneName}', 'width', this.value)">
                            Высота: <input type="number" id="height-${zoneName}" value="${Math.round(zoneHeight)}" onchange="updateZone('${zoneName}', 'height', this.value)">
                            <button onclick="selectZone('${zoneName}')">Выбрать</button>
                        </div>
                    `;
                    editorContainer.appendChild(editor);
                }
            }
        }
        
        // Выбор зоны
        function selectZone(zoneName) {
            selectedZone = zoneName;
            renderZones();
            const zone = zones[zoneName];
            const height = zone.height || zone.max_height || 0;
            document.getElementById('info').textContent = `Выбрана зона: ${zoneName}. Координаты: X=${zone.x}, Y=${zone.y}, Ш=${zone.width}, В=${height}`;
        }
        
        // Обновление координаты зоны
        function updateZone(zoneName, prop, value) {
            if (zones[zoneName]) {
                zones[zoneName][prop] = parseInt(value) || 0;
                const zone = zones[zoneName];
                const height = zone.height || zone.max_height || 0;
                
                // Ограничиваем значения
                if (prop === 'x') {
                    zones[zoneName].x = Math.max(0, Math.min(zones[zoneName].x, canvas.width - zones[zoneName].width));
                } else if (prop === 'y') {
                    zones[zoneName].y = Math.max(0, Math.min(zones[zoneName].y, canvas.height - height));
                } else if (prop === 'width') {
                    zones[zoneName].width = Math.max(50, Math.min(zones[zoneName].width, canvas.width - zones[zoneName].x));
                } else if (prop === 'height' || prop === 'max_height') {
                    // Для date_block используем height, для дней - max_height
                    if (zoneName === 'date_block') {
                        zones[zoneName].height = Math.max(20, Math.min(zones[zoneName].height, canvas.height - zones[zoneName].y));
                    } else {
                        zones[zoneName].max_height = Math.max(50, Math.min(zones[zoneName].max_height, canvas.height - zones[zoneName].y));
                    }
                }
                renderZones();
            }
        }
        
        // Перетаскивание и изменение размера
        let resizeHandle = null;
        let initialZone = null;
        
        document.addEventListener('mousemove', (e) => {
            if (isDragging && selectedZone) {
                const rect = canvas.getBoundingClientRect();
                const mouseX = e.clientX - rect.left;
                const mouseY = e.clientY - rect.top;
                
                if (resizeHandle) {
                    // Изменение размера
                    const zone = zones[selectedZone];
                    const isDateBlock = selectedZone === 'date_block';
                    const heightProp = isDateBlock ? 'height' : 'max_height';
                    const minHeight = isDateBlock ? 20 : 50;
                    
                    if (resizeHandle === 'se') {
                        // Правый нижний угол
                        zone.width = Math.max(50, Math.min(mouseX - zone.x, canvas.width - zone.x));
                        zone[heightProp] = Math.max(minHeight, Math.min(mouseY - zone.y, canvas.height - zone.y));
                    } else if (resizeHandle === 'sw') {
                        // Левый нижний угол
                        const newWidth = zone.x + zone.width - mouseX;
                        if (newWidth >= 50 && mouseX >= 0) {
                            zone.width = newWidth;
                            zone.x = mouseX;
                        }
                        zone[heightProp] = Math.max(minHeight, Math.min(mouseY - zone.y, canvas.height - zone.y));
                    } else if (resizeHandle === 'ne') {
                        // Правый верхний угол
                        zone.width = Math.max(50, Math.min(mouseX - zone.x, canvas.width - zone.x));
                        const currentHeight = zone[heightProp] || minHeight;
                        const newHeight = zone.y + currentHeight - mouseY;
                        if (newHeight >= minHeight && mouseY >= 0) {
                            zone[heightProp] = newHeight;
                            zone.y = mouseY;
                        }
                    } else if (resizeHandle === 'nw') {
                        // Левый верхний угол
                        const newWidth = zone.x + zone.width - mouseX;
                        if (newWidth >= 50 && mouseX >= 0) {
                            zone.width = newWidth;
                            zone.x = mouseX;
                        }
                        const currentHeight = zone[heightProp] || minHeight;
                        const newHeight = zone.y + currentHeight - mouseY;
                        if (newHeight >= minHeight && mouseY >= 0) {
                            zone[heightProp] = newHeight;
                            zone.y = mouseY;
                        }
                    } else if (resizeHandle === 'e') {
                        // Правая сторона
                        zone.width = Math.max(50, Math.min(mouseX - zone.x, canvas.width - zone.x));
                    } else if (resizeHandle === 'w') {
                        // Левая сторона
                        const newWidth = zone.x + zone.width - mouseX;
                        if (newWidth >= 50 && mouseX >= 0) {
                            zone.width = newWidth;
                            zone.x = mouseX;
                        }
                    } else if (resizeHandle === 's') {
                        // Нижняя сторона
                        zone[heightProp] = Math.max(minHeight, Math.min(mouseY - zone.y, canvas.height - zone.y));
                    } else if (resizeHandle === 'n') {
                        // Верхняя сторона
                        const currentHeight = zone[heightProp] || minHeight;
                        const newHeight = zone.y + currentHeight - mouseY;
                        if (newHeight >= minHeight && mouseY >= 0) {
                            zone[heightProp] = newHeight;
                            zone.y = mouseY;
                        }
                    }
                } else {
                    // Перемещение
                    const x = mouseX - dragOffset.x;
                    const y = mouseY - dragOffset.y;
                    const zone = zones[selectedZone];
                    const height = zone.height || zone.max_height || 40;
                    
                    zones[selectedZone].x = Math.max(0, Math.min(x, canvas.width - zones[selectedZone].width));
                    zones[selectedZone].y = Math.max(0, Math.min(y, canvas.height - height));
                }
                
                renderZones();
                updateZoneInputs(selectedZone);
            }
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
            resizeHandle = null;
        });
        
        function updateZoneInputs(zoneName) {
            if (zones[zoneName]) {
                const zone = zones[zoneName];
                document.getElementById('x-' + zoneName).value = Math.round(zone.x);
                document.getElementById('y-' + zoneName).value = Math.round(zone.y);
                document.getElementById('width-' + zoneName).value = Math.round(zone.width);
                const height = zone.height || zone.max_height || 40;
                document.getElementById('height-' + zoneName).value = Math.round(height);
            }
        }
        
        // Изменение размера зоны (двойной клик для изменения размеров)
        let resizeMode = null;
        
        // Сохранение зон
        async function saveZones() {
            try {
                const response = await fetch('/api/zones', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(zones)
                });
                
                if (response.ok) {
                    document.getElementById('info').textContent = '✅ Координаты успешно сохранены!';
                    setTimeout(() => {
                        document.getElementById('info').textContent = 'Координаты сохранены. Можно продолжить редактирование.';
                    }, 2000);
                } else {
                    throw new Error('Ошибка сохранения');
                }
            } catch (error) {
                document.getElementById('info').textContent = '❌ Ошибка сохранения: ' + error.message;
            }
        }
        
        // Сброс изменений
        function resetZones() {
            loadZones();
            document.getElementById('info').textContent = 'Изменения сброшены.';
        }
        
        // Перезагрузка из файла
        function reloadZones() {
            loadZones();
            document.getElementById('info').textContent = 'Зоны перезагружены из файла.';
        }
        
        // Удаление выбранной зоны
        function deleteSelectedZone() {
            if (selectedZone && confirm(`Удалить зону ${selectedZone}?`)) {
                delete zones[selectedZone];
                selectedZone = null;
                renderZones();
                document.getElementById('info').textContent = 'Зона удалена.';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

@app.route('/api/zones', methods=['GET'])
def get_zones():
    """Загружает зоны из YAML файла."""
    try:
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        zones = {}
        # Фильтруем дни недели
        for day in ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']:
            if data.get(day):
                zones[day] = data[day]
        
        # Добавляем date_block если есть
        if data.get('date_block'):
            zones['date_block'] = data['date_block']
        
        return jsonify(zones)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/zones', methods=['POST'])
def save_zones():
    """Сохраняет зоны в YAML файл."""
    try:
        zones = request.json
        
        # Загружаем существующий файл
        with open(ZONES_FILE, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        # Обновляем зоны дней недели
        for day in ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ']:
            if day in zones:
                # Конвертируем координаты в целые числа
                zone_data = zones[day].copy()
                zone_data['x'] = int(round(zone_data.get('x', 0)))
                zone_data['y'] = int(round(zone_data.get('y', 0)))
                zone_data['width'] = int(round(zone_data.get('width', 0)))
                zone_data['max_height'] = int(round(zone_data.get('max_height', 0)))
                data[day] = zone_data
        
        # Обновляем date_block если есть
        if 'date_block' in zones:
            zone_data = zones['date_block'].copy()
            zone_data['x'] = int(round(zone_data.get('x', 0)))
            zone_data['y'] = int(round(zone_data.get('y', 0)))
            zone_data['width'] = int(round(zone_data.get('width', 0)))
            zone_data['height'] = int(round(zone_data.get('height', zone_data.get('max_height', 32))))
            # Убираем max_height если есть, используем только height
            if 'max_height' in zone_data:
                del zone_data['max_height']
            data['date_block'] = zone_data
        
        # Сохраняем обратно
        with open(ZONES_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Редактор зон меню запущен!")
    print("Откройте в браузере: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)

