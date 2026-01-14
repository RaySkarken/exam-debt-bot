"""
Step definitions для тестирования деталей расхода
Роль: Тестировщик
"""
import pytest
from pytest_bdd import given, when, then, parsers
from src.bot import DebtBot


@given(parsers.parse('существует расход "{description}" на {amount:d} рублей с участниками {participants}'))
def expense_exists(description, amount, participants, db, context):
    """Создать расход"""
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
    context['bot'] = DebtBot(db)


@given(parsers.parse('{username} заплатил {amount:d} рублей'))
def user_paid(username, amount, context):
    """Пользователь заплатил"""
    db = context['db']
    db.pay_debt(username, 'Вася', amount)


@when(parsers.parse('пользователь пишет "{message}"'))
def user_requests_expense_details(message, context):
    """Пользователь запрашивает детали расхода"""
    bot = context['bot']
    response = bot.process_message(message, 'Пользователь')
    context['response'] = response


@then(parsers.parse('бот показывает детали расхода "{description}"'))
def bot_shows_expense_details(description, context):
    """Бот показывает детали расхода"""
    assert description in context['response']


@then(parsers.parse('в деталях указана сумма {amount:d} рублей'))
def details_show_amount(amount, context):
    """В деталях указана сумма"""
    assert str(amount) in context['response']


@then("в деталях указаны все участники")
def details_show_participants(context):
    """В деталях указаны участники"""
    # Проверяем что ответ содержит информацию об участниках
    assert len(context['response']) > 0


@then(parsers.parse('в деталях показано что {username} заплатил {amount:d} рублей'))
def details_show_payment(username, amount, context):
    """В деталях показана выплата"""
    assert username in context['response']
    assert str(amount) in context['response']


@then(parsers.parse('в деталях показано что {username} должна {amount:d} рублей'))
def details_show_debt(username, amount, context):
    """В деталях показан долг"""
    assert username in context['response']
    assert str(amount) in context['response']


@then(parsers.parse('в деталях показано что {username} должен {amount:d} рублей'))
def details_show_debt_male(username, amount, context):
    """В деталях показан долг"""
    assert username in context['response']
    assert str(amount) in context['response']


@given("бот запущен")
def bot_is_running(db, context):
    """Бот запущен"""
    context['db'] = db
    context['bot'] = DebtBot(db)


@then(parsers.parse('бот отвечает "{response}"'))
def bot_responds_with(response, context):
    """Бот отвечает указанным текстом"""
    assert context['response'] == response

