"""
Unit тесты для keyboards.py
Роль: Тестировщик
"""
import pytest
from src.keyboards import (
    get_main_menu_keyboard,
    get_debts_keyboard,
    get_payment_confirmation_keyboard,
    get_back_to_menu_keyboard,
    get_expense_list_keyboard
)


def test_get_main_menu_keyboard():
    """Тест создания главного меню"""
    keyboard = get_main_menu_keyboard()
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) > 0
    
    # Проверяем наличие основных кнопок
    buttons_text = []
    for row in keyboard.inline_keyboard:
        for button in row:
            buttons_text.append(button.text)
    
    assert "📝 Создать расход" in buttons_text
    assert "💳 Мои долги" in buttons_text
    assert "📊 Статистика" in buttons_text
    assert "📜 История" in buttons_text


def test_get_debts_keyboard():
    """Тест создания клавиатуры долгов"""
    debts = [
        {'creditor': 'Вася', 'remaining': 1000, 'description': 'пицца'},
        {'creditor': 'Петя', 'remaining': 500, 'description': 'кофе'}
    ]
    
    keyboard = get_debts_keyboard('Пользователь', debts)
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= len(debts) + 1  # +1 для кнопки "Назад"
    
    # Проверяем наличие кнопки "Назад"
    has_back = False
    for row in keyboard.inline_keyboard:
        for button in row:
            if "Назад" in button.text or "◀️" in button.text:
                has_back = True
    assert has_back


def test_get_payment_confirmation_keyboard():
    """Тест создания клавиатуры подтверждения выплаты"""
    keyboard = get_payment_confirmation_keyboard('Петя', 'Вася', 1000)
    assert keyboard is not None
    
    # Проверяем наличие кнопки подтверждения
    has_confirm = False
    for row in keyboard.inline_keyboard:
        for button in row:
            if "Подтвердить" in button.text or "✅" in button.text:
                has_confirm = True
    assert has_confirm


def test_get_back_to_menu_keyboard():
    """Тест создания кнопки возврата в меню"""
    keyboard = get_back_to_menu_keyboard()
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 1
    assert "Главное меню" in keyboard.inline_keyboard[0][0].text or "◀️" in keyboard.inline_keyboard[0][0].text


def test_get_expense_list_keyboard():
    """Тест создания клавиатуры списка расходов"""
    expenses = [
        {'id': 1, 'description': 'пицца', 'total_amount': 4200},
        {'id': 2, 'description': 'кофе', 'total_amount': 600}
    ]
    
    keyboard = get_expense_list_keyboard(expenses)
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) >= len(expenses) + 1  # +1 для кнопки "Назад"

