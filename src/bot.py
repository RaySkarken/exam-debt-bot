"""
Telegram бот для отслеживания долгов
Роль: Разработчик
"""
import re
from typing import Optional, Dict
from src.database import Database


class DebtBot:
    """Класс для обработки команд бота"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def parse_expense_command(self, message: str, creator_username: str) -> Optional[str]:
        """
        Парсит команду создания расхода
        Формат: "описание сумма @участник1 @участник2 ..."
        
        Returns:
            Ответ бота или None если команда не распознана
        """
        # Паттерн: слово, число, упоминания
        pattern = r'^(\w+)\s+(\d+(?:\.\d+)?)\s+(.+)$'
        match = re.match(pattern, message)
        
        if not match:
            return None
        
        description = match.group(1)
        try:
            amount = float(match.group(2))
        except ValueError:
            return "Неверный формат суммы. Используйте число"
        
        participants_text = match.group(3)
        # Извлекаем упоминания
        participants = re.findall(r'@(\w+)', participants_text)
        
        if not participants:
            return "Укажите участников через @"
        
        # Создаём расход
        expense_id = self.db.create_expense(
            description=description,
            total_amount=amount,
            creator_username=creator_username,
            participants=participants
        )
        
        amount_per_person = amount / len(participants)
        
        if len(participants) == 1:
            return f"Записал! {participants[0]} должен {int(amount_per_person)}р"
        else:
            return f"Записал! По {int(amount_per_person)}р с каждого. Общий долг: {int(amount)}р"
    
    def parse_payment_command(self, message: str, debtor_username: str) -> Optional[str]:
        """
        Парсит команду выплаты долга
        Формат: "скинул @кредитор сумма" или "скинул кредитор сумма"
        
        Returns:
            Ответ бота или None если команда не распознана
        """
        # Паттерн: "скинул" + имя + сумма
        pattern = r'скинул\s+@?(\w+)\s+(\d+(?:\.\d+)?)'
        match = re.match(pattern, message)
        
        if not match:
            return None
        
        creditor_username = match.group(1)
        try:
            amount = float(match.group(2))
        except ValueError:
            return "Неверный формат суммы"
        
        # Проверяем текущий долг
        current_debt = self.db.get_debt_amount(debtor_username, creditor_username)
        
        if current_debt == 0:
            return f"У вас нет долга перед {creditor_username}"
        
        if amount > current_debt:
            return f"Сумма выплаты ({int(amount)}р) больше долга ({int(current_debt)}р)"
        
        # Выплачиваем долг
        success = self.db.pay_debt(debtor_username, creditor_username, amount)
        
        if not success:
            return f"Ошибка при выплате долга"
        
        # Проверяем остаток
        remaining_debt = self.db.get_debt_amount(debtor_username, creditor_username)
        
        if remaining_debt == 0:
            # Полностью погашен
            remaining_debts = self.db.get_debts(creditor_username=creditor_username)
            remaining_names = []
            for debt in remaining_debts:
                if debt['debtor'] != debtor_username:
                    remaining_names.append(f"{debt['debtor']} ({int(debt['remaining'])}р)")
            
            if remaining_names:
                names_str = ', '.join(remaining_names)
                return f"Принял! {debtor_username} больше не должен. Остались: {names_str}"
            else:
                return f"Принял! {debtor_username} больше не должен."
        else:
            return f"Принял! {debtor_username} должен ещё {int(remaining_debt)}р"
    
    def parse_debts_command(self, message: str) -> Optional[str]:
        """
        Парсит команду просмотра долгов
        Формат: "долги" или "долги @кредитор"
        
        Returns:
            Ответ бота или None если команда не распознана
        """
        if message.strip() == "долги":
            debts = self.db.get_debts()
            
            if not debts:
                return "Нет активных долгов 🎉"
            
            debt_lines = []
            for debt in debts:
                days = (debt['created_at'] - debt['created_at']).days if hasattr(debt['created_at'], 'days') else 0
                from datetime import datetime
                if isinstance(debt['created_at'], datetime):
                    days = (datetime.now() - debt['created_at']).days
                
                overdue = " ⚠️ ПРОСРОЧЕНО" if days > 7 else ""
                debt_lines.append(f"{debt['debtor']} должен {debt['creditor']} {int(debt['remaining'])}р" + overdue)
            
            return '\n'.join(debt_lines)
        
        # "долги @кредитор"
        pattern = r'долги\s+@?(\w+)'
        match = re.match(pattern, message)
        
        if match:
            creditor_username = match.group(1)
            debts = self.db.get_debts(creditor_username=creditor_username)
            
            if not debts:
                return f"Нет долгов перед {creditor_username}"
            
            debt_lines = []
            for debt in debts:
                debt_lines.append(f"{debt['debtor']} должен {debt['creditor']} {int(debt['remaining'])}р")
            
            return '\n'.join(debt_lines)
        
        return None
    
    def process_message(self, message: str, username: str) -> str:
        """
        Обрабатывает сообщение пользователя
        
        Args:
            message: Текст сообщения
            username: Имя пользователя
        
        Returns:
            Ответ бота
        """
        message = message.strip()
        
        # Пробуем разные команды
        response = self.parse_expense_command(message, username)
        if response:
            return response
        
        response = self.parse_payment_command(message, username)
        if response:
            return response
        
        response = self.parse_debts_command(message)
        if response:
            return response
        
        # Статистика
        if message.strip() == "статистика":
            stats = self.db.get_statistics()
            return f"""📊 Общая статистика:
• Активных долгов: {stats['debt_count']}
• Общая сумма: {int(stats['total_debt'])}р
• Должников: {stats['debtors_count']}
• Кредиторов: {stats['creditors_count']}"""
        
        # Статистика по пользователю
        pattern = r'статистика\s+@?(\w+)'
        match = re.match(pattern, message)
        if match:
            username = match.group(1)
            stats = self.db.get_statistics(username=username)
            return f"""📊 Статистика для {username}:
• Активных долгов: {stats['debt_count']}
• Общая сумма: {int(stats['total_debt'])}р"""
        
        # История операций
        if message.strip() == "история":
            history = self.db.get_operation_history(limit=20)
            if not history:
                return "История пуста"
            
            history_lines = []
            for op in history:
                date_str = op['created_at'].strftime('%d.%m %H:%M')
                history_lines.append(f"{date_str} | {op['username']}: {op['description']}")
            
            return "📜 История операций:\n" + '\n'.join(history_lines)
        
        # История конкретного расхода
        pattern = r'история\s+(\w+)'
        match = re.match(pattern, message)
        if match:
            description = match.group(1)
            expense = self.db.get_expense_by_description(description)
            if not expense:
                return f"Расход '{description}' не найден"
            
            history = self.db.get_operation_history(expense_id=expense['id'])
            if not history:
                return f"История расхода '{description}' пуста"
            
            history_lines = []
            for op in history:
                date_str = op['created_at'].strftime('%d.%m %H:%M')
                history_lines.append(f"{date_str} | {op['username']}: {op['description']}")
            
            return f"📜 История расхода '{description}':\n" + '\n'.join(history_lines)
        
        # Детали расхода
        pattern = r'расход\s+(\w+)'
        match = re.match(pattern, message)
        if match:
            description = match.group(1)
            expense = self.db.get_expense_by_description(description)
            if not expense:
                return "Расход не найден"
            
            lines = [
                f"📋 Расход: {expense['description']}",
                f"💰 Сумма: {int(expense['total_amount'])}р",
                f"👤 Создатель: {expense['creator_username']}",
                f"📅 Создан: {expense['created_at'].strftime('%d.%m.%Y %H:%M')}",
                "",
                "💳 Долги:"
            ]
            
            for debt in expense['debts']:
                if debt['remaining'] > 0:
                    lines.append(f"  • {debt['debtor']} должен {debt['creditor']} {int(debt['remaining'])}р")
                else:
                    lines.append(f"  ✅ {debt['debtor']} заплатил {int(debt['paid'])}р")
            
            return '\n'.join(lines)
        
        # Долги по расходам (группировка)
        if message.strip() == "долги по расходам":
            grouped = self.db.get_debts_grouped_by_expense()
            
            if not grouped:
                return "Нет активных долгов 🎉"
            
            lines = []
            for description, debts in grouped.items():
                lines.append(f"\n📦 {description}:")
                for debt in debts:
                    lines.append(f"  • {debt['debtor']} должен {debt['creditor']} {int(debt['remaining'])}р")
            
            return "💳 Долги по расходам:" + '\n'.join(lines)
        
        # Отмена расхода
        pattern = r'отменить\s+(\w+)'
        match = re.match(pattern, message)
        if match:
            description = match.group(1)
            expense = self.db.get_expense_by_description(description)
            
            if not expense:
                return "Расход не найден"
            
            # Проверяем что пользователь - создатель
            success = self.db.cancel_expense(expense['id'], username)
            
            if not success:
                return "Вы не можете отменить этот расход. Только создатель может отменить"
            
            return f"Расход '{description}' отменён. Все долги удалены"
        
        # Неизвестная команда
        return """Доступные команды:
• "описание сумма @участник1 @участник2" - создать расход
• "скинул @кредитор сумма" - выплатить долг
• "долги" - показать все долги
• "долги @кредитор" - долги конкретному человеку
• "долги по расходам" - долги сгруппированные по расходам
• "расход описание" - детали расхода
• "история" - история операций
• "история описание" - история конкретного расхода
• "отменить описание" - отменить расход (только создатель)
• "статистика" - общая статистика
• "статистика @пользователь" - статистика по пользователю"""

