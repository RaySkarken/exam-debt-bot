#!/bin/bash
# Скрипт для запуска тестов в Docker
# Роль: DevOps - автоматизация тестирования

set -e

echo "🧪 Запуск тестов в Docker..."

# Проверяем наличие docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose не найден. Установите Docker Compose."
    exit 1
fi

# Останавливаем старые контейнеры если есть
docker-compose -f docker-compose.test.yml down 2>/dev/null || true

# Удаляем старую тестовую БД если есть
rm -f test_debts.db

# Запускаем тесты
echo "📦 Запуск тестового окружения..."
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit test-runner

# Сохраняем код выхода
EXIT_CODE=$?

# Останавливаем контейнеры
echo "🛑 Остановка тестового окружения..."
docker-compose -f docker-compose.test.yml down

# Возвращаем код выхода
exit $EXIT_CODE

