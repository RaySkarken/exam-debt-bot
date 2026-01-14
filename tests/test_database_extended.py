"""
Расширенные тесты для database.py
Роль: Тестировщик - увеличение покрытия
"""
import pytest
from src.database import Database
import tempfile
import os


@pytest.fixture
def db():
    """Фикстура для создания временной БД"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    database = Database(db_path=path)
    database.init_db()
    yield database
    os.unlink(path)


def test_get_debt_amount(db):
    """Тест получения суммы долга"""
    # Создаём расход
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    # Проверяем сумму долга
    debt = db.get_debt_amount("Петя", "Вася")
    assert debt == 2000


def test_get_debt_amount_no_debt(db):
    """Тест получения суммы несуществующего долга"""
    debt = db.get_debt_amount("Петя", "Вася")
    assert debt == 0


def test_get_debts_with_creditor(db):
    """Тест получения долгов конкретному кредитору"""
    # Создаём расходы
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    db.create_expense("кофе", 600, "Петя", ["Маша"])
    
    # Получаем долги Васе
    debts = db.get_debts(creditor_username="Вася")
    assert len(debts) == 1
    assert debts[0]['creditor'] == "Вася"
    assert debts[0]['debtor'] == "Петя"


def test_pay_debt_partial(db):
    """Тест частичной выплаты долга"""
    # Создаём расход
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    # Выплачиваем часть
    success = db.pay_debt("Петя", "Вася", 1000)
    assert success is True
    
    # Проверяем остаток
    remaining = db.get_debt_amount("Петя", "Вася")
    assert remaining == 1000


def test_pay_debt_full(db):
    """Тест полной выплаты долга"""
    # Создаём расход
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    # Выплачиваем полностью
    success = db.pay_debt("Петя", "Вася", 2000)
    assert success is True
    
    # Проверяем что долг погашен
    remaining = db.get_debt_amount("Петя", "Вася")
    assert remaining == 0


def test_pay_debt_more_than_owed(db):
    """Тест выплаты больше чем долг"""
    # Создаём расход
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    # Пытаемся выплатить больше
    success = db.pay_debt("Петя", "Вася", 3000)
    # Должно вернуть False или обработать корректно
    assert success is False or db.get_debt_amount("Петя", "Вася") == 0


def test_get_statistics_with_data(db):
    """Тест получения статистики с данными"""
    # Создаём расходы
    db.create_expense("пицца", 2000, "Вася", ["Петя", "Маша"])
    db.create_expense("кофе", 600, "Петя", ["Маша"])
    
    stats = db.get_statistics()
    assert stats['debt_count'] > 0
    assert stats['total_debt'] > 0


def test_get_statistics_empty(db):
    """Тест получения статистики без данных"""
    stats = db.get_statistics()
    assert stats['debt_count'] == 0
    assert stats['total_debt'] == 0


def test_get_operation_history(db):
    """Тест получения истории операций"""
    # Создаём расход
    expense_id = db.create_expense("пицца", 2000, "Вася", ["Петя"])
    
    # Получаем историю
    history = db.get_operation_history()
    assert len(history) > 0
    
    # Проверяем что есть запись о создании расхода
    expense_history = [h for h in history if h['expense_id'] == expense_id]
    assert len(expense_history) > 0


def test_get_debts_grouped_by_expense(db):
    """Тест получения долгов сгруппированных по расходам"""
    # Создаём несколько расходов
    db.create_expense("пицца", 2000, "Вася", ["Петя"])
    db.create_expense("кофе", 600, "Петя", ["Маша"])
    
    grouped = db.get_debts_grouped_by_expense()
    assert len(grouped) > 0
    assert "пицца" in grouped or "кофе" in grouped

