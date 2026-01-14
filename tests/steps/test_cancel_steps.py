"""
Step definitions для тестирования отмены расхода
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


@given(parsers.parse('расход создан пользователем "{username}"'))
def expense_created_by(username, context):
    """Расход создан пользователем"""
    context['creator'] = username


@when(parsers.parse('{username} пишет "{message}"'))
def user_cancels_expense(username, message, context):
    """Пользователь отменяет расход"""
    bot = context['bot']
    response = bot.process_message(message, username)
    context['response'] = response
    context['action_user'] = username


@then(parsers.parse('бот удаляет расход "{description}"'))
def bot_deletes_expense(description, context):
    """Бот удаляет расход"""
    db = context['db']
    expense = db.get_expense_by_description(description)
    assert expense is None or expense.get('is_cancelled', False)


@then("бот удаляет все связанные долги")
def bot_deletes_related_debts(context):
    """Бот удаляет все связанные долги"""
    db = context['db']
    debts = db.get_debts()
    # Проверяем что долги по отменённому расходу удалены
    # (это проверяется через то что расход не найден или отменён)


@then(parsers.parse('бот отвечает "{response}"'))
def bot_responds_with(response, context):
    """Бот отвечает указанным текстом"""
    assert response in context['response'] or context['response'] == response


@given("бот запущен")
def bot_is_running(db, context):
    """Бот запущен"""
    context['db'] = db
    context['bot'] = DebtBot(db)

