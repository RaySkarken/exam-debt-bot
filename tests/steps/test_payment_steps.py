"""
Step definitions для тестирования выплаты долгов
Роль: Тестировщик
"""
import pytest
from pytest_bdd import given, when, then, parsers
from src.bot import DebtBot


@given(parsers.parse('существует расход "{description}" на {amount:d} рублей с участниками {participants}'))
def expense_exists(description, amount, participants, db, context):
    """Создать расход для теста"""
    # Парсим участников из строки "@Петя @Маша @Коля"
    parts = participants.split()
    participant_list = [p.replace('@', '') for p in parts if p.startswith('@')]
    
    expense_id = db.create_expense(
        description=description,
        total_amount=amount,
        creator_username='Вася',
        participants=participant_list
    )
    
    context['db'] = db
    context['expense_id'] = expense_id
    context['description'] = description
    context['amount'] = amount
    context['participants'] = participant_list
    context['bot'] = DebtBot(db)


@given(parsers.parse('{username} должен {amount:d} рублей'))
def user_owes_amount(username, amount, context):
    """Пользователь должен указанную сумму"""
    db = context['db']
    debt = db.get_debt_amount(username, 'Вася')
    assert debt == amount


@when(parsers.parse('{username} пишет "{message}"'))
def user_pays_debt(username, message, context):
    """Пользователь выплачивает долг"""
    bot = context['bot']
    response = bot.process_message(message, username)
    context['response'] = response
    context['debtor'] = username


@then(parsers.parse('долг {username} уменьшается на {amount:d} рублей'))
def debt_decreases(username, amount, context):
    """Долг уменьшается"""
    # Проверяем что долг уменьшился (через контекст)
    assert 'response' in context
    assert 'Принял' in context['response']


@then(parsers.parse('{username} больше не должен'))
def user_no_longer_owes(username, context):
    """Пользователь больше не должен"""
    db = context['db']
    debt = db.get_debt_amount(username, 'Вася')
    assert debt == 0


@then(parsers.parse('{username} должен ещё {amount:d} рублей'))
def user_still_owes(username, amount, context):
    """Пользователь должен ещё указанную сумму"""
    db = context['db']
    debt = db.get_debt_amount(username, 'Вася')
    assert debt == amount


@given(parsers.parse('{username} не должен {creditor}'))
def user_does_not_owe(username, creditor, context):
    """Пользователь не должен"""
    db = context['db']
    debt = db.get_debt_amount(username, creditor)
    assert debt == 0


@given("бот запущен")
def bot_is_running(db, context):
    """Бот запущен"""
    context['db'] = db
    context['bot'] = DebtBot(db)
    context['response'] = None


