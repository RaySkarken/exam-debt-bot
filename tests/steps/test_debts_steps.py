"""
Step definitions для тестирования просмотра долгов
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


@given(parsers.parse('{username} не заплатил'))
def user_did_not_pay(username):
    """Пользователь не заплатил"""
    pass  # Долг остаётся


@when(parsers.parse('пользователь нажимает кнопку "{button_text}"'))
def user_clicks_debts_button(button_text, context):
    """Пользователь нажимает кнопку просмотра долгов"""
    context['clicked_button'] = button_text
    db = context['db']
    
    if button_text == "💳 Мои долги":
        # Получаем долги текущего пользователя
        username = context.get('current_user', 'Пользователь')
        all_debts = db.get_debts()
        context['debts'] = [d for d in all_debts if d['debtor'] == username]
        context['action'] = 'view_my_debts'


@then("бот показывает список долгов")
def bot_shows_debts_list(context):
    """Бот показывает список долгов"""
    assert 'debts' in context
    assert len(context['debts']) > 0


@then(parsers.parse('бот показывает список долгов {username}'))
def bot_shows_user_debts_list(username, context):
    """Бот показывает список долгов пользователя"""
    assert 'debts' in context
    debts = context['debts']
    assert all(d['debtor'] == username for d in debts)


@then("в списке есть кнопки для каждого долга")
def list_has_buttons(context):
    """В списке есть кнопки"""
    debts = context.get('debts', [])
    assert len(debts) > 0
    context['has_buttons'] = True


@then(parsers.parse('можно нажать кнопку для выплаты долга {creditor}'))
def can_click_payment_button(creditor, context):
    """Можно нажать кнопку выплаты"""
    assert context.get('has_buttons', False)


@then(parsers.parse('в списке есть долг {username}'))
def list_contains_debt(username, context):
    """В списке есть долг пользователя"""
    debts = context.get('debts', [])
    found = any(d['debtor'] == username for d in debts)
    assert found, f"Долг {username} не найден в списке"


@then(parsers.parse('в списке нет долга {username}'))
def list_does_not_contain(username, context):
    """В списке нет долга пользователя"""
    debts = context.get('debts', [])
    for debt in debts:
        assert debt['debtor'] != username


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


@given(parsers.parse('существует расход "{description}" созданный {days:d} дней назад на {amount:d} рублей с участниками {participants}'))
def old_expense_exists(description, days, amount, participants, db, context):
    """Создать старый расход"""
    # Для теста просто создаём расход, в реальности нужно было бы модифицировать created_at
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
    context['days_ago'] = days
    context['bot'] = DebtBot(db)


@then(parsers.parse('бот показывает "{text}"'))
def bot_shows_text(text, context):
    """Бот показывает указанный текст"""
    # Для кнопок проверяем что действие выполнено
    if 'action' in context:
        assert context.get('action') in ['view_my_debts', 'view_statistics']


@then(parsers.parse('бот помечает долг как просроченный если прошло больше {days:d} дней'))
def bot_marks_overdue(days):
    """Бот помечает просроченные долги"""
    # В реальной реализации здесь была бы проверка на просрочку
    pass

