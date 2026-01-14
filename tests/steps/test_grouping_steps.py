"""
Step definitions для тестирования группировки долгов
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


@when(parsers.parse('пользователь пишет "{message}"'))
def user_requests_grouped_debts(message, context):
    """Пользователь запрашивает долги по расходам"""
    bot = context['bot']
    response = bot.process_message(message, 'Пользователь')
    context['response'] = response


@then("бот показывает долги сгруппированные по расходам")
def bot_shows_grouped_debts(context):
    """Бот показывает долги сгруппированные по расходам"""
    assert 'response' in context
    assert len(context['response']) > 0


@then(parsers.parse('в списке есть группа "{description}"'))
def list_contains_group(description, context):
    """В списке есть группа"""
    assert description in context['response']


@then(parsers.parse('в группе "{description}" показаны долги {participants}'))
def group_shows_debts(description, participants, context):
    """В группе показаны долги"""
    # Проверяем что описание есть в ответе
    assert description in context['response']
    # Проверяем что участники упомянуты
    parts = participants.split()
    for part in parts:
        if part.startswith('@'):
            username = part.replace('@', '')
            assert username in context['response']


@given("бот запущен")
def bot_is_running(db, context):
    """Бот запущен"""
    context['db'] = db
    context['bot'] = DebtBot(db)


@given("нет активных долгов")
def no_active_debts(context):
    """Нет активных долгов"""
    db = context['db']
    debts = db.get_debts()
    assert len(debts) == 0


@then(parsers.parse('бот отвечает "{response}"'))
def bot_responds_with(response, context):
    """Бот отвечает указанным текстом"""
    assert context['response'] == response

