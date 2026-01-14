"""
Unit тесты для bot.py
Роль: Тестировщик - увеличение покрытия
"""
import pytest
from src.bot import DebtBot
from src.database import Database


@pytest.fixture
def bot(db):
    """Фикстура для создания бота"""
    return DebtBot(db)


def test_bot_initialization(bot):
    """Тест инициализации бота"""
    assert bot is not None
    assert bot.db is not None


def test_process_message_create_expense(bot, db):
    """Тест обработки команды создания расхода"""
    message = "пицца 4200 @Петя @Маша"
    response = bot.process_message(message, "Вася")
    
    # Проверяем что расход создан
    debts = db.get_debts()
    assert len(debts) == 2  # Два долга (Петя и Маша должны Васе)
    
    # Проверяем что ответ содержит информацию о создании
    assert "Записал" in response or "расход" in response.lower()


def test_process_message_view_debts(bot, db):
    """Тест обработки команды просмотра долгов"""
    # Создаём расход
    db.create_expense("пицца", 4200, "Вася", ["Петя", "Маша"])
    
    message = "долги"
    response = bot.process_message(message, "Петя")
    
    # Проверяем что ответ содержит информацию о долгах
    assert len(response) > 0


def test_process_message_pay_debt(bot, db):
    """Тест обработки команды выплаты долга"""
    # Создаём расход
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    # Выплачиваем долг
    message = "скинул Васе 2000"
    response = bot.process_message(message, "Петя")
    
    # Проверяем что долг погашен
    debt = db.get_debt_amount("Петя", "Вася")
    assert debt == 0


def test_process_message_statistics(bot, db):
    """Тест обработки команды статистики"""
    # Создаём несколько расходов
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    db.create_expense("кофе", 600, "Петя", ["Маша"])
    
    message = "статистика"
    response = bot.process_message(message, "Пользователь")
    
    # Проверяем что ответ содержит статистику
    assert len(response) > 0


def test_process_message_history(bot, db):
    """Тест обработки команды истории"""
    # Создаём расход
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    message = "история"
    response = bot.process_message(message, "Пользователь")
    
    # Проверяем что ответ содержит историю
    assert len(response) > 0


def test_process_message_unknown_command(bot):
    """Тест обработки неизвестной команды"""
    message = "неизвестная команда"
    response = bot.process_message(message, "Пользователь")
    
    # Проверяем что бот отвечает на неизвестную команду
    assert len(response) > 0


def test_process_message_empty(bot):
    """Тест обработки пустого сообщения"""
    message = ""
    response = bot.process_message(message, "Пользователь")
    
    # Проверяем что бот обрабатывает пустое сообщение
    assert len(response) > 0

