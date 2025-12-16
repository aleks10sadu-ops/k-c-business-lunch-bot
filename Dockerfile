FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей (для Pillow)
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директорий для вывода
RUN mkdir -p output

# Переменная окружения для токена
ENV BOT_TOKEN=""

# Запуск бота
CMD ["python", "-m", "bot.main"]

