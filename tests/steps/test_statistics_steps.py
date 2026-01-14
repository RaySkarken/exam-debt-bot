"""
Step definitions для тестирования статистики
Роль: Тестировщик - обновлено для работы с кнопками
"""
import pytest
from pytest_bdd import given, when, then, parsers
from src.bot import DebtBot


@given("существует несколько расходов с разными участниками")
def multiple_expenses_exist(db, context):
    """Создать несколько расходов"""
    # Создаём расходы
    db.create_expense("пицца", 4200, "Вася", ["Петя", "Маша"])
    db.create_expense("кофе", 600, "Петя", ["Маша", "Коля"])
    
    context['db'] = db
    context['bot'] = DebtBot(db)


@when(parsers.parse('пользователь нажимает кнопку "{button_text}"'))
def user_clicks_statistics_button(button_text, context):
    """Пользователь нажимает кнопку статистики"""
    context['clicked_button'] = button_text
    if button_text == "📊 Статистика":
        context['action'] = 'view_statistics'
        db = context['db']
        context['statistics'] = db.get_statistics()


@then("бот показывает общую сумму всех долгов")
def bot_shows_total_debt(context):
    """Бот показывает общую сумму"""
    stats = context.get('statistics', {})
    assert 'total_debt' in stats


@then("бот показывает количество активных долгов")
def bot_shows_debt_count(context):
    """Бот показывает количество долгов"""
    stats = context.get('statistics', {})
    assert 'debt_count' in stats


@then("бот показывает количество должников")
def bot_shows_debtors_count(context):
    """Бот показывает количество должников"""
    stats = context.get('statistics', {})
    assert 'debtors_count' in stats


@then("бот показывает количество кредиторов")
def bot_shows_creditors_count(context):
    """Бот показывает количество кредиторов"""
    stats = context.get('statistics', {})
    assert 'creditors_count' in stats

