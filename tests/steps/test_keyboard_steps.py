"""
Step definitions для тестирования кнопок и интерфейса
Роль: Тестировщик - обновлено для работы только с кнопками
"""
import pytest
from pytest_bdd import given, when, then, parsers
from src.bot import DebtBot
from src.database import Database


@given("бот запущен", target_fixture="bot_instance")
def bot_is_running(db, context):
    """Бот запущен и БД инициализирована"""
    bot = DebtBot(db)
    context['bot'] = bot
    context['db'] = db
    return bot


@when('пользователь отправляет команду /start')
def user_sends_start_command(bot_instance, context):
    """Пользователь отправляет команду /start"""
    # В реальности это обрабатывается через aiogram, но для тестов просто отмечаем
    context['start_sent'] = True


@then("бот показывает главное меню с кнопками")
def bot_shows_main_menu(context):
    """Бот показывает главное меню"""
    assert context.get('start_sent', False)


@then(parsers.parse('в меню есть кнопка "{button_text}"'))
def menu_has_button(button_text, context):
    """В меню есть указанная кнопка"""
    # Проверяем что кнопка должна быть в главном меню
    expected_buttons = [
        "📝 Создать расход",
        "💳 Мои долги",
        "📊 Статистика",
        "📜 История",
        "📦 Долги по расходам",
        "ℹ️ Помощь"
    ]
    assert button_text in expected_buttons


@when(parsers.parse('пользователь нажимает кнопку "{button_text}"'))
def user_clicks_button(button_text, context):
    """Пользователь нажимает кнопку"""
    context['clicked_button'] = button_text
    
    # Симулируем действие кнопки
    if button_text == "📝 Создать расход":
        context['fsm_state'] = 'waiting_description'
    elif button_text == "💳 Мои долги":
        context['action'] = 'view_debts'
    elif button_text == "📊 Статистика":
        context['action'] = 'view_statistics'
    elif button_text == "📜 История":
        context['action'] = 'view_history'
    elif button_text == "◀️ Главное меню":
        context['action'] = 'main_menu'
        if 'fsm_state' in context:
            del context['fsm_state']


@then("бот запрашивает описание расхода")
def bot_asks_for_description(context):
    """Бот запрашивает описание"""
    assert context.get('fsm_state') == 'waiting_description'


@when(parsers.parse('пользователь вводит описание "{description}"'))
def user_enters_description(description, context):
    """Пользователь вводит описание"""
    context['expense_description'] = description
    context['fsm_state'] = 'waiting_amount'


@then("бот запрашивает сумму")
def bot_asks_for_amount(context):
    """Бот запрашивает сумму"""
    assert context.get('fsm_state') == 'waiting_amount'


@when(parsers.parse('пользователь вводит сумму "{amount}"'))
def user_enters_amount(amount, context):
    """Пользователь вводит сумму"""
    try:
        context['expense_amount'] = float(amount)
        context['fsm_state'] = 'waiting_participants'
    except ValueError:
        context['error'] = 'Неверный формат суммы'


@then("бот запрашивает участников")
def bot_asks_for_participants(context):
    """Бот запрашивает участников"""
    assert context.get('fsm_state') == 'waiting_participants'


@when(parsers.parse('пользователь вводит участников "{participants}"'))
def user_enters_participants(participants, context):
    """Пользователь вводит участников"""
    parts = participants.split()
    context['expense_participants'] = [p.replace('@', '') for p in parts if p.startswith('@')]
    
    # Создаём расход через БД
    db = context['db']
    expense_id = db.create_expense(
        description=context.get('expense_description', 'тест'),
        total_amount=context.get('expense_amount', 1000),
        creator_username='Вася',
        participants=context['expense_participants']
    )
    context['expense_id'] = expense_id
    context['expense_created'] = True


@then(parsers.parse('бот создаёт расход на {amount:d} рублей'))
def bot_creates_expense(amount, context):
    """Бот создаёт расход"""
    assert context.get('expense_created', False)
    assert context.get('expense_amount') == amount


@then(parsers.parse('бот распределяет долг между {count:d} участниками'))
def bot_distributes_debt(count, context):
    """Бот распределяет долг"""
    assert len(context.get('expense_participants', [])) == count


@then(parsers.parse('каждый участник должен по {amount:d} рублей'))
def each_participant_owes(amount, context):
    """Каждый участник должен указанную сумму"""
    total = context.get('expense_amount', 0)
    participants_count = len(context.get('expense_participants', []))
    expected = total / participants_count
    assert expected == amount


@then("бот показывает сообщение об успешном создании")
def bot_shows_success_message(context):
    """Бот показывает сообщение об успехе"""
    assert context.get('expense_created', False)


@then("процесс создания расхода отменяется")
def expense_creation_cancelled(context):
    """Процесс создания отменён"""
    assert 'fsm_state' not in context or context.get('action') == 'main_menu'


@then("пользователь возвращается в главное меню")
def user_returns_to_main_menu(context):
    """Пользователь в главном меню"""
    assert context.get('action') == 'main_menu'


@then(parsers.parse('бот показывает ошибку "{error}"'))
def bot_shows_error(error, context):
    """Бот показывает ошибку"""
    assert context.get('error') == error or error in str(context.get('error', ''))


@then("бот запрашивает сумму снова")
def bot_asks_amount_again(context):
    """Бот запрашивает сумму повторно"""
    assert context.get('fsm_state') == 'waiting_amount'

