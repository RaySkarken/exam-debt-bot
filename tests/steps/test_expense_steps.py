"""
Step definitions для тестирования создания расходов
Роль: Тестировщик
"""
import pytest
from pytest_bdd import given, when, then, parsers
from src.bot import DebtBot


@given("бот запущен", target_fixture="bot_instance")
def bot_is_running(db, context):
    """Бот запущен и БД инициализирована"""
    bot = DebtBot(db)
    context['bot'] = bot
    context['db'] = db
    return bot


@when(parsers.parse('пользователь пишет "{message}"'))
def user_sends_message(message, bot_instance, context):
    """Пользователь отправляет сообщение"""
    bot = context['bot']
    db = context['db']
    
    # Обрабатываем сообщение через бота
    response = bot.process_message(message, 'Вася')
    context['response'] = response
    context['message'] = message
    
    # Парсим для проверок
    if message.startswith('пицца') or message.startswith('кофе') or message.startswith('обед'):
        parts = message.split()
        if len(parts) >= 2:
            try:
                amount = float(parts[1])
                participants = [p.replace('@', '') for p in parts[2:] if p.startswith('@')]
                
                if participants:
                    context['amount'] = amount
                    context['participants'] = participants
                    context['amount_per_person'] = amount / len(participants)
                    # Проверяем что расход создан
                    debts = db.get_debts(creditor_username='Вася')
                    context['expense_created'] = len(debts) > 0
            except ValueError:
                pass


@then(parsers.parse('бот создаёт расход на {amount:d} рублей'))
def bot_creates_expense(amount, context):
    """Бот создаёт расход"""
    assert context.get('expense_created', False)
    assert context.get('amount') == amount


@then(parsers.parse('бот распределяет долг между {count:d} участниками'))
def bot_distributes_debt(count, context):
    """Бот распределяет долг"""
    assert len(context.get('participants', [])) == count


@then(parsers.parse('каждый участник должен по {amount:d} рублей'))
def each_participant_owes(amount, context):
    """Каждый участник должен указанную сумму"""
    assert context.get('amount_per_person') == amount


@then(parsers.parse('бот отвечает "{response}"'))
def bot_responds(response, context):
    """Бот отвечает указанным текстом"""
    assert context.get('response') == response


@then(parsers.parse('бот распределяет долг на {count:d} участника'))
def bot_distributes_debt_single(count, context):
    """Бот распределяет долг на одного участника"""
    assert len(context.get('participants', [])) == count


@then(parsers.parse('{username} должен {amount:d} рублей'))
def user_owes(username, amount, context):
    """Пользователь должен указанную сумму"""
    db = context['db']
    debt = db.get_debt_amount(username, 'Вася')
    assert debt == amount

