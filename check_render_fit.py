# -*- coding: utf-8 -*-
"""
Самопроверка: подобранный размер шрифта помещает ВСЕ блюда с описаниями в зону.
Ловит регрессию, из-за которой описания пропадали (расчёт высоты != реальный рендер).
Запуск: python check_render_fit.py  (exit 0 = ок, 1 = что-то не влезло)
"""
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw
import yaml

from renderer.image_renderer import ImageRenderer

with open("config/settings.yaml", encoding="utf-8") as f:
    settings = yaml.safe_load(f)
with open("config/zones.yaml", encoding="utf-8") as f:
    zones = yaml.safe_load(f)

# Худший реальный случай: 6 блюд с длинными описаниями (меню 06.07–10.07, ПН)
DISHES = [
    {"title": "ЧИКАГО", "desc": "колбаса, грибы, сыр, яйцо, огурец маринованный, лук, специи, майонез"},
    {"title": "ГРЕЧЕСКИЙ", "desc": "огурец, помидор, перец, лук красный, оливки, маслины, сыр чанах, масло, соль, перец, лимон"},
    {"title": "ОКРОШКА НА КВАСЕ/АЙРАНЕ", "desc": "картофель, редис, яйцо, огурец, колбаса, зелень, лук, хрен, горчица"},
    {"title": "ЩИ ИЗ КВАШЕНОЙ КАПУСТЫ", "desc": "говядина, лук, морковь, картофель, сметана, помидор, зелень, капуста квашенная"},
    {"title": "ЗРАЗЫ С СЫРОМ", "desc": "куриный фарш, сыр, специи, лук"},
    {"title": "ГУЛЯШ ИЗ СВИНИНЫ", "desc": "свинина, лук, морковь, томат, специи"},
]

renderer = ImageRenderer(
    settings["template"]["image"], zones,
    settings["fonts"], settings["layout"], settings.get("warning_block"),
)
zone = zones["ПН"]
_, _, tl, dl = renderer._calculate_optimal_font_sizes(DISHES, zone["width"], zone["max_height"])

# Повторяем продвижение по вертикали ровно так, как это делает _render_day_menu
draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
aw, ah = zone["width"] - 4, zone["max_height"] - 4
between = settings["layout"].get("between_dishes_spacing", 10)
cur = 0
for idx, dish in enumerate(DISHES):
    tlines = tl.wrap_text(dish["title"].upper(), aw)
    ly = cur
    for line in tlines[:-1]:
        bb = draw.textbbox((0, ly), line, font=tl.font)
        ly += (bb[3] - bb[1]) + tl.line_spacing
    cur = draw.textbbox((0, ly), tlines[-1], font=tl.font)[3] + 1
    assert cur <= ah - 3, f"описание блюда '{dish['title']}' не влезает (y={cur} > {ah - 3})"
    cur += dl.calculate_text_height(dl.wrap_text(dish["desc"], aw))
    if idx < len(DISHES) - 1:
        cur += between
    assert cur <= ah - 3 or idx == len(DISHES) - 1, \
        f"после '{dish['title']}' зона переполнена (y={cur} > {ah - 3})"

print(f"OK: все {len(DISHES)} блюд с описаниями помещаются ({cur}/{ah - 3}px)")
sys.exit(0)
