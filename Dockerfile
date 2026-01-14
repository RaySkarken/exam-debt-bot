# Dockerfile для приложения управления долгами
# Роль: DevOps - контейнеризация приложения

FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка браузеров для Playwright (для E2E тестов)
RUN playwright install chromium || true
RUN playwright install-deps chromium || true

# Копирование исходного кода
COPY . .

# Создание директории для БД (если нужно)
RUN mkdir -p /app/data

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открытие портов
# 5000 - Flask веб-приложение
EXPOSE 5000

# Команда по умолчанию (запуск веб-приложения)
# Для запуска бота используйте docker-compose или переопределите CMD
CMD ["python", "src/web/app.py"]

