from flask import Flask, request, send_file
from PIL import Image, ImageDraw, ImageFont
import io
import random

app = Flask(__name__)

# === НАСТРОЙКИ (ТЕПЕРЬ ПО НАЧАЛУ КЛЕТОК) ===
FONT_PATH = "Caveat-Regular.ttf"            # Используем твой вытащенный шрифт
BG_PATH = "notebook.jpg"          # Твоя обрезанная тетрадь
FONT_SIZE = 22                    # Оставляем этот размер, он хорош
LINE_SPACING = 28                 # Оптимальный интервал
START_X = 55      # Твой идеальный отступ слева (не трогаем)
START_Y = 15      # <--- Уменьшили, чтобы поднять текст на самый верх!
MAX_WIDTH = 340                   # Оставляем перенос на новую строку вниз
@app.route('/gen', methods=['POST'])
def generate_image():
    text = request.form.get('text', 'Текст не найден')

    try:
        # Пытаемся открыть фон
        try:
            bg = Image.open(BG_PATH).convert("RGBA")
        except IOError:
            return f"❌ Ошибка: Не могу найти картинку '{BG_PATH}'", 500

        txt_layer = Image.new("RGBA", bg.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(txt_layer)
        
        # Пытаемся открыть шрифт
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except IOError:
            return f"❌ Ошибка: Не могу прочитать шрифт '{FONT_PATH}' (возможно, файл битый)", 500

        x, y = START_X, START_Y
        words = text.split()
        
        for word in words:
            word += " "
            word_width = draw.textlength(word, font=font)
            
            # Перенос на новую строку
            if x + word_width > START_X + MAX_WIDTH:
                x = START_X
                y += LINE_SPACING

            # Рисуем по буквам (эффект живой руки)
            for char in word:
                char_width = draw.textlength(char, font=font)
                y_jitter = random.randint(-2, 1) # Дрожание руки по вертикали
                pen_color = (21, 11, 110, random.randint(180, 255)) # Меняем нажим ручки
                draw.text((x, y + y_jitter), char, font=font, fill=pen_color)
                x += char_width
            
        final_img = Image.alpha_composite(bg, txt_layer).convert("RGB")
        img_io = io.BytesIO()
        final_img.save(img_io, 'JPEG', quality=90)
        img_io.seek(0)

        return send_file(img_io, mimetype='image/jpeg')

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)