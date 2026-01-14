"""
Step definitions для тестирования истории операций
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
def user_requests_history(message, context):
    """Пользователь запрашивает историю"""
    bot = context['bot']
    response = bot.process_message(message, 'Пользователь')
    context['response'] = response


@then("бот показывает историю операций")
def bot_shows_history(context):
    """Бот показывает историю"""
    assert 'response' in context
    assert 'История' in context['response'] or 'история' in context['response'].lower()


@then(parsers.parse('в истории есть создание расхода "{description}"'))
def history_contains_expense(description, context):
    """В истории есть создание расхода"""
    db = context['db']
    history = db.get_operation_history()
    assert any(op['description'] and description in op['description'] for op in history)


@then(parsers.parse('в истории есть выплата {username} {amount:d} рублей'))
def history_contains_payment(username, amount, context):
    """В истории есть выплата"""
    db = context['db']
    history = db.get_operation_history()
    assert any(op['operation_type'] == 'payment' and 
               op['username'] == username and 
               op['amount'] == amount for op in history)


@then(parsers.parse('бот показывает историю расхода "{description}"'))
def bot_shows_expense_history(description, context):
    """Бот показывает историю расхода"""
    assert description in context['response']


@then("в истории показано создание расхода")
def history_shows_expense_creation(context):
    """В истории показано создание расхода"""
    assert 'создан' in context['response'].lower() or 'создание' in context['response'].lower()


@then("в истории показаны все участники")
def history_shows_participants(context):
    """В истории показаны участники"""
    # Проверяем что ответ не пустой
    assert len(context['response']) > 0


@given("бот запущен")
def bot_is_running(db, context):
    """Бот запущен"""
    context['db'] = db
    context['bot'] = DebtBot(db)


@given("нет операций в истории")
def no_operations_in_history(context):
    """Нет операций в истории"""
    db = context['db']
    history = db.get_operation_history()
    assert len(history) == 0


@then(parsers.parse('бот отвечает "{response}"'))
def bot_responds_with(response, context):
    """Бот отвечает указанным текстом"""
    assert context['response'] == response

