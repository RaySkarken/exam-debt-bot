"""
Точка входа для Telegram бота
"""
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from src.database import Database
from src.bot import DebtBot

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


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "💰 Бот для отслеживания долгов\n\n"
        "Основные команды:\n"
        "• \"пицца 4200 @Петя @Маша\" - создать расход\n"
        "• \"скинул Васе 700\" - выплатить долг\n"
        "• \"долги\" - показать все долги\n"
        "• \"долги @Вася\" - долги конкретному человеку\n"
        "• \"долги по расходам\" - долги сгруппированные\n\n"
        "Дополнительно:\n"
        "• \"расход пицца\" - детали расхода\n"
        "• \"история\" - история операций\n"
        "• \"отменить пицца\" - отменить расход\n"
        "• \"статистика\" - статистика"
    )


@dp.message()
async def handle_message(message: types.Message):
    """Обработчик всех сообщений"""
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    text = message.text or ""
    
    response = debt_bot.process_message(text, username)
    await message.answer(response)


async def main():
    """Главная функция"""
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

