"""
Модуль для создания клавиатур Telegram бота
Роль: Архитектор - проектирование структуры меню и кнопок
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict, Optional


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню с основными действиями
    
    Returns:
        InlineKeyboardMarkup с кнопками главного меню
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Создать расход", callback_data="create_expense"),
            InlineKeyboardButton(text="💳 Мои долги", callback_data="my_debts")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="statistics"),
            InlineKeyboardButton(text="📜 История", callback_data="history")
        ],
        [
            InlineKeyboardButton(text="📦 Долги по расходам", callback_data="debts_by_expense"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ])
    return keyboard


def get_debts_keyboard(debtor_username: str, debts: List[Dict]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком долгов и кнопками для выплаты
    
    Args:
        debtor_username: Имя должника
        debts: Список долгов
    
    Returns:
        InlineKeyboardMarkup с кнопками долгов
    """
    buttons = []
    for debt in debts[:10]:  # Ограничиваем 10 долгами
        creditor = debt['creditor']
        remaining = int(debt['remaining'])
        description = debt.get('description', 'расход')
        button_text = f"💸 {creditor}: {remaining}р ({description[:15]})"
        callback_data = f"pay_debt:{debtor_username}:{creditor}:{remaining}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Кнопка "Назад"
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_expense_list_keyboard(expenses: List[Dict]) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком расходов
    
    Args:
        expenses: Список расходов
    
    Returns:
        InlineKeyboardMarkup с кнопками расходов
    """
    buttons = []
    for expense in expenses[:10]:
        description = expense['description']
        amount = int(expense['total_amount'])
        button_text = f"📋 {description} ({amount}р)"
        callback_data = f"expense_details:{expense['id']}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_confirmation_keyboard(debtor: str, creditor: str, amount: float) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения выплаты
    
    Args:
        debtor: Должник
        creditor: Кредитор
        amount: Сумма
    
    Returns:
        InlineKeyboardMarkup с кнопками подтверждения
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"✅ Подтвердить выплату {int(amount)}р",
                callback_data=f"confirm_payment:{debtor}:{creditor}:{amount}"
            )
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_payment"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="my_debts")
        ]
    ])
    return keyboard


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Простая клавиатура с кнопкой "Назад в меню" """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="main_menu")]
    ])


def get_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Reply keyboard для быстрого доступа к основным командам
    
    Returns:
        ReplyKeyboardMarkup с основными кнопками
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💳 Долги"),
                KeyboardButton(text="📊 Статистика")
            ],
            [
                KeyboardButton(text="📜 История"),
                KeyboardButton(text="📦 По расходам")
            ],
            [
                KeyboardButton(text="ℹ️ Помощь"),
                KeyboardButton(text="📝 Создать")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или введите команду"
    )
    return keyboard

