"""
Точка входа для Telegram бота
Роль: Разработчик - интеграция кнопок и обработчиков
"""
import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from dotenv import load_dotenv
from src.database import Database
from src.bot import DebtBot
from src.keyboards import (
    get_main_menu_keyboard,
    get_debts_keyboard,
    get_expense_list_keyboard,
    get_payment_confirmation_keyboard,
    get_back_to_menu_keyboard,
    get_reply_keyboard
)

# Загружаем переменные окружения
load_dotenv()

# Инициализация
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в .env файле")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация БД и бота
db = Database()
debt_bot = DebtBot(db)

# Состояния для создания расхода (FSM)
user_states = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = (
        "💰 Бот для отслеживания долгов\n\n"
        "Используйте кнопки ниже для быстрого доступа к функциям!\n\n"
        "Или введите команды текстом:\n"
        "• \"пицца 4200 @Петя @Маша\" - создать расход\n"
        "• \"скинул Васе 700\" - выплатить долг\n"
        "• \"долги\" - показать все долги"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_reply_keyboard()
    )
    await message.answer(
        "📱 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )


# Обработчики callback кнопок
@dp.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Обработчик кнопки 'Главное меню'"""
    await callback.message.edit_text(
        "📱 Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "my_debts")
async def callback_my_debts(callback: CallbackQuery):
    """Обработчик кнопки 'Мои долги'"""
    username = callback.from_user.username or callback.from_user.first_name or "Unknown"
    debts = db.get_debts()
    
    # Фильтруем долги текущего пользователя
    user_debts = [d for d in debts if d['debtor'] == username]
    
    if not user_debts:
        await callback.message.edit_text(
            "🎉 У вас нет активных долгов!",
            reply_markup=get_back_to_menu_keyboard()
        )
    else:
        total = sum(d['remaining'] for d in user_debts)
        text = f"💳 Ваши долги (всего: {int(total)}р):\n\n"
        text += "\n".join([
            f"• {d['creditor']}: {int(d['remaining'])}р ({d['description']})"
            for d in user_debts[:5]
        ])
        if len(user_debts) > 5:
            text += f"\n\n... и ещё {len(user_debts) - 5} долгов"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_debts_keyboard(username, user_debts)
        )
    await callback.answer()


@dp.callback_query(F.data == "statistics")
async def callback_statistics(callback: CallbackQuery):
    """Обработчик кнопки 'Статистика'"""
    stats = db.get_statistics()
    text = f"""📊 Общая статистика:
• Активных долгов: {stats['debt_count']}
• Общая сумма: {int(stats['total_debt'])}р
• Должников: {stats['debtors_count']}
• Кредиторов: {stats['creditors_count']}"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "history")
async def callback_history(callback: CallbackQuery):
    """Обработчик кнопки 'История'"""
    history = db.get_operation_history(limit=10)
    
    if not history:
        text = "История пуста"
    else:
        text = "📜 Последние операции:\n\n"
        for op in history:
            date_str = op['created_at'].strftime('%d.%m %H:%M')
            text += f"{date_str} | {op['username']}: {op['description']}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "debts_by_expense")
async def callback_debts_by_expense(callback: CallbackQuery):
    """Обработчик кнопки 'Долги по расходам'"""
    grouped = db.get_debts_grouped_by_expense()
    
    if not grouped:
        text = "Нет активных долгов 🎉"
    else:
        text = "💳 Долги по расходам:\n\n"
        for description, debts in list(grouped.items())[:5]:
            text += f"📦 {description}:\n"
            for debt in debts[:3]:
                text += f"  • {debt['debtor']} должен {debt['creditor']} {int(debt['remaining'])}р\n"
            text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery):
    """Обработчик кнопки 'Помощь'"""
    help_text = (
        "ℹ️ Помощь\n\n"
        "📝 Создать расход:\n"
        "Нажмите кнопку или напишите:\n"
        "\"пицца 4200 @Петя @Маша\"\n\n"
        "💸 Выплатить долг:\n"
        "Нажмите на долг в списке или напишите:\n"
        "\"скинул Васе 700\"\n\n"
        "💳 Просмотр долгов:\n"
        "Используйте кнопки или команду \"долги\"\n\n"
        "📊 Статистика:\n"
        "Показывает общую информацию о долгах"
    )
    await callback.message.edit_text(
        help_text,
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("pay_debt:"))
async def callback_pay_debt(callback: CallbackQuery):
    """Обработчик кнопки выплаты долга"""
    _, debtor, creditor, amount = callback.data.split(":")
    amount = float(amount)
    
    text = f"💸 Выплата долга\n\n"
    text += f"Должник: {debtor}\n"
    text += f"Кредитор: {creditor}\n"
    text += f"Сумма: {int(amount)}р\n\n"
    text += "Подтвердите выплату:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_confirmation_keyboard(debtor, creditor, amount)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_payment:"))
async def callback_confirm_payment(callback: CallbackQuery):
    """Обработчик подтверждения выплаты"""
    _, debtor, creditor, amount = callback.data.split(":")
    amount = float(amount)
    
    username = callback.from_user.username or callback.from_user.first_name or "Unknown"
    
    # Проверяем что пользователь - должник
    if username != debtor:
        await callback.answer("Вы можете выплачивать только свои долги!", show_alert=True)
        return
    
    # Выплачиваем долг
    success = db.pay_debt(debtor, creditor, amount)
    
    if success:
        remaining = db.get_debt_amount(debtor, creditor)
        if remaining == 0:
            text = f"✅ Долг полностью погашен!\n\n{debtor} больше не должен {creditor}"
        else:
            text = f"✅ Частичная выплата принята!\n\nОстаток долга: {int(remaining)}р"
    else:
        text = "❌ Ошибка при выплате долга"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer("Выплата обработана!")


@dp.callback_query(F.data == "cancel_payment")
async def callback_cancel_payment(callback: CallbackQuery):
    """Обработчик отмены выплаты"""
    await callback.message.edit_text(
        "❌ Выплата отменена",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "create_expense")
async def callback_create_expense(callback: CallbackQuery):
    """Обработчик кнопки создания расхода"""
    user_id = callback.from_user.id
    user_states[user_id] = {"step": "waiting_description", "data": {}}
    
    await callback.message.edit_text(
        "📝 Создание расхода\n\n"
        "Введите описание расхода (например: пицца):",
        reply_markup=get_back_to_menu_keyboard()
    )
    await callback.answer()


@dp.message()
async def handle_message(message: types.Message):
    """Обработчик всех сообщений"""
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    user_id = message.from_user.id
    text = message.text or ""
    
    # Обработка reply keyboard кнопок
    if text == "💳 Долги":
        debts = db.get_debts()
        user_debts = [d for d in debts if d['debtor'] == username]
        if user_debts:
            total = sum(d['remaining'] for d in user_debts)
            response = f"💳 Ваши долги (всего: {int(total)}р):\n\n"
            response += "\n".join([
                f"• {d['creditor']}: {int(d['remaining'])}р"
                for d in user_debts[:10]
            ])
        else:
            response = "🎉 У вас нет активных долгов!"
        await message.answer(response, reply_markup=get_main_menu_keyboard())
        return
    
    elif text == "📊 Статистика":
        stats = db.get_statistics()
        response = f"""📊 Общая статистика:
• Активных долгов: {stats['debt_count']}
• Общая сумма: {int(stats['total_debt'])}р
• Должников: {stats['debtors_count']}
• Кредиторов: {stats['creditors_count']}"""
        await message.answer(response, reply_markup=get_main_menu_keyboard())
        return
    
    elif text == "📜 История":
        history = db.get_operation_history(limit=10)
        if history:
            response = "📜 Последние операции:\n\n"
            for op in history:
                date_str = op['created_at'].strftime('%d.%m %H:%M')
                response += f"{date_str} | {op['username']}: {op['description']}\n"
        else:
            response = "История пуста"
        await message.answer(response, reply_markup=get_main_menu_keyboard())
        return
    
    elif text == "📦 По расходам":
        grouped = db.get_debts_grouped_by_expense()
        if grouped:
            response = "💳 Долги по расходам:\n\n"
            for description, debts in list(grouped.items())[:5]:
                response += f"📦 {description}:\n"
                for debt in debts[:3]:
                    response += f"  • {debt['debtor']} должен {debt['creditor']} {int(debt['remaining'])}р\n"
                response += "\n"
        else:
            response = "Нет активных долгов 🎉"
        await message.answer(response, reply_markup=get_main_menu_keyboard())
        return
    
    elif text == "ℹ️ Помощь":
        await message.answer(
            "ℹ️ Используйте кнопки для быстрого доступа или введите команды текстом",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    elif text == "📝 Создать":
        user_states[user_id] = {"step": "waiting_description", "data": {}}
        await message.answer(
            "📝 Создание расхода\n\nВведите описание расхода (например: пицца):",
            reply_markup=get_back_to_menu_keyboard()
        )
        return
    
    # Обработка состояний создания расхода
    if user_id in user_states:
        state = user_states[user_id]
        if state["step"] == "waiting_description":
            state["data"]["description"] = text
            state["step"] = "waiting_amount"
            await message.answer("Введите сумму (например: 4200):")
            return
        elif state["step"] == "waiting_amount":
            try:
                amount = float(text)
                state["data"]["amount"] = amount
                state["step"] = "waiting_participants"
                await message.answer("Введите участников через @ (например: @Петя @Маша):")
                return
            except ValueError:
                await message.answer("Неверный формат суммы. Введите число:")
                return
        elif state["step"] == "waiting_participants":
            participants = [p.replace('@', '') for p in text.split() if p.startswith('@')]
            if not participants:
                await message.answer("Укажите участников через @ (например: @Петя @Маша):")
                return
            
            # Создаём расход
            expense_id = db.create_expense(
                description=state["data"]["description"],
                total_amount=state["data"]["amount"],
                creator_username=username,
                participants=participants
            )
            
            amount_per_person = state["data"]["amount"] / len(participants)
            response = f"✅ Расход создан!\n\n"
            response += f"Описание: {state['data']['description']}\n"
            response += f"Сумма: {int(state['data']['amount'])}р\n"
            response += f"По {int(amount_per_person)}р с каждого"
            
            del user_states[user_id]
            await message.answer(response, reply_markup=get_main_menu_keyboard())
            return
    
    # Обычная обработка текстовых команд
    response = debt_bot.process_message(text, username)
    await message.answer(response, reply_markup=get_main_menu_keyboard())


async def main():
    """Главная функция"""
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

