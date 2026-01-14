"""
Модуль для работы с базой данных SQLite
Архитектор: проектирование схемы БД
"""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Expense:
    """Модель расхода"""
    id: int
    description: str
    total_amount: float
    creator_username: str
    created_at: datetime
    participants: List[str]


@dataclass
class Debt:
    """Модель долга"""
    id: int
    expense_id: int
    debtor_username: str
    creditor_username: str
    amount: float
    paid_amount: float
    created_at: datetime


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = "debts.db"):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Инициализация схемы БД"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица расходов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                total_amount REAL NOT NULL,
                creator_username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_cancelled INTEGER DEFAULT 0
            )
        """)
        
        # Таблица долгов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS debts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                debtor_username TEXT NOT NULL,
                creditor_username TEXT NOT NULL,
                amount REAL NOT NULL,
                paid_amount REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expense_id) REFERENCES expenses(id)
            )
        """)
        
        # Таблица истории операций
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER,
                operation_type TEXT NOT NULL,
                username TEXT NOT NULL,
                description TEXT,
                amount REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expense_id) REFERENCES expenses(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_expense(self, description: str, total_amount: float, 
                      creator_username: str, participants: List[str]) -> int:
        """
        Создать расход и распределить долги
        
        Args:
            description: Описание расхода
            total_amount: Общая сумма
            creator_username: Кто создал (кредитор)
            participants: Список участников (должников)
        
        Returns:
            ID созданного расхода
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Создаём расход
        cursor.execute("""
            INSERT INTO expenses (description, total_amount, creator_username)
            VALUES (?, ?, ?)
        """, (description, total_amount, creator_username))
        
        expense_id = cursor.lastrowid
        
        # Распределяем долги
        amount_per_person = total_amount / len(participants)
        for participant in participants:
            cursor.execute("""
                INSERT INTO debts (expense_id, debtor_username, creditor_username, amount)
                VALUES (?, ?, ?, ?)
            """, (expense_id, participant, creator_username, amount_per_person))
        
        # Записываем в историю
        cursor.execute("""
            INSERT INTO operation_history (expense_id, operation_type, username, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (expense_id, 'expense_created', creator_username, 
              f"Создан расход '{description}' на {total_amount}р", total_amount))
        
        conn.commit()
        conn.close()
        
        return expense_id
    
    def pay_debt(self, debtor_username: str, creditor_username: str, 
                 amount: float) -> bool:
        """
        Выплатить долг
        
        Args:
            debtor_username: Кто платит
            creditor_username: Кому платит
            amount: Сумма выплаты
        
        Returns:
            True если успешно, False если долга нет или сумма больше долга
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Находим активные долги
        cursor.execute("""
            SELECT id, amount, paid_amount
            FROM debts
            WHERE debtor_username = ? AND creditor_username = ?
            AND (amount - paid_amount) > 0
            ORDER BY created_at
        """, (debtor_username, creditor_username))
        
        debts = cursor.fetchall()
        
        if not debts:
            conn.close()
            return False
        
        remaining = amount
        expense_id = None
        for debt in debts:
            debt_id = debt['id']
            debt_amount = debt['amount']
            paid = debt['paid_amount']
            remaining_debt = debt_amount - paid
            
            # Получаем expense_id для истории
            if expense_id is None:
                cursor.execute("SELECT expense_id FROM debts WHERE id = ?", (debt_id,))
                exp_row = cursor.fetchone()
                if exp_row:
                    expense_id = exp_row['expense_id']
            
            if remaining >= remaining_debt:
                # Полностью погашаем долг
                cursor.execute("""
                    UPDATE debts
                    SET paid_amount = amount
                    WHERE id = ?
                """, (debt_id,))
                remaining -= remaining_debt
            else:
                # Частично погашаем
                cursor.execute("""
                    UPDATE debts
                    SET paid_amount = paid_amount + ?
                    WHERE id = ?
                """, (remaining, debt_id))
                remaining = 0
                break
        
        # Записываем в историю
        cursor.execute("""
            INSERT INTO operation_history (expense_id, operation_type, username, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (expense_id, 'payment', debtor_username, 
              f"Выплата {amount}р {creditor_username}", amount))
        
        conn.commit()
        conn.close()
        return True
    
    def get_debts(self, creditor_username: Optional[str] = None) -> List[Dict]:
        """
        Получить список долгов
        
        Args:
            creditor_username: Если указан, только долги этому человеку
        
        Returns:
            Список словарей с информацией о долгах
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if creditor_username:
            cursor.execute("""
                SELECT 
                    d.id,
                    d.debtor_username,
                    d.creditor_username,
                    d.amount,
                    d.paid_amount,
                    (d.amount - d.paid_amount) as remaining,
                    d.created_at,
                    e.description
                FROM debts d
                JOIN expenses e ON d.expense_id = e.id
                WHERE d.creditor_username = ? AND (d.amount - d.paid_amount) > 0 
                AND e.is_cancelled = 0
                ORDER BY d.created_at
            """, (creditor_username,))
        else:
            cursor.execute("""
                SELECT 
                    d.id,
                    d.debtor_username,
                    d.creditor_username,
                    d.amount,
                    d.paid_amount,
                    (d.amount - d.paid_amount) as remaining,
                    d.created_at,
                    e.description
                FROM debts d
                JOIN expenses e ON d.expense_id = e.id
                WHERE (d.amount - d.paid_amount) > 0 AND e.is_cancelled = 0
                ORDER BY d.created_at
            """)
        
        debts = []
        for row in cursor.fetchall():
            # Парсим дату из SQLite формата
            created_at_str = row['created_at']
            try:
                created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    created_at = datetime.now()
            
            debts.append({
                'id': row['id'],
                'debtor': row['debtor_username'],
                'creditor': row['creditor_username'],
                'amount': row['amount'],
                'paid': row['paid_amount'],
                'remaining': row['remaining'],
                'created_at': created_at,
                'description': row['description']
            })
        
        conn.close()
        return debts
    
    def get_statistics(self, username: Optional[str] = None) -> Dict:
        """
        Получить статистику по долгам
        
        Args:
            username: Если указан, статистика для конкретного пользователя
        
        Returns:
            Словарь со статистикой
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if username:
            # Статистика для конкретного пользователя
            cursor.execute("""
                SELECT 
                    COUNT(*) as debt_count,
                    SUM(amount - paid_amount) as total_debt
                FROM debts
                WHERE debtor_username = ? AND (amount - paid_amount) > 0
            """, (username,))
        else:
            # Общая статистика
            cursor.execute("""
                SELECT 
                    COUNT(*) as debt_count,
                    SUM(amount - paid_amount) as total_debt,
                    COUNT(DISTINCT debtor_username) as debtors_count,
                    COUNT(DISTINCT creditor_username) as creditors_count
                FROM debts
                WHERE (amount - paid_amount) > 0
            """)
        
        result = cursor.fetchone()
        conn.close()
        
        stats = {
            'debt_count': result['debt_count'] or 0,
            'total_debt': result['total_debt'] or 0.0
        }
        
        if not username:
            stats['debtors_count'] = result['debtors_count'] or 0
            stats['creditors_count'] = result['creditors_count'] or 0
        
        return stats
    
    def add_operation_history(self, operation_type: str, username: str, 
                              description: str, amount: Optional[float] = None,
                              expense_id: Optional[int] = None):
        """
        Добавить запись в историю операций
        
        Args:
            operation_type: Тип операции (expense_created, payment, expense_cancelled)
            username: Кто выполнил операцию
            description: Описание операции
            amount: Сумма (опционально)
            expense_id: ID расхода (опционально)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO operation_history (expense_id, operation_type, username, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, (expense_id, operation_type, username, description, amount))
        
        conn.commit()
        conn.close()
    
    def get_operation_history(self, expense_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """
        Получить историю операций
        
        Args:
            expense_id: Если указан, только операции по этому расходу
            limit: Максимальное количество записей
        
        Returns:
            Список операций
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if expense_id:
            cursor.execute("""
                SELECT * FROM operation_history
                WHERE expense_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (expense_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM operation_history
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
        
        operations = []
        for row in cursor.fetchall():
            created_at_str = row['created_at']
            try:
                created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                except:
                    created_at = datetime.now()
            
            operations.append({
                'id': row['id'],
                'expense_id': row['expense_id'],
                'operation_type': row['operation_type'],
                'username': row['username'],
                'description': row['description'],
                'amount': row['amount'],
                'created_at': created_at
            })
        
        conn.close()
        return operations
    
    def get_expense_details(self, expense_id: int) -> Optional[Dict]:
        """
        Получить детали расхода
        
        Args:
            expense_id: ID расхода
        
        Returns:
            Словарь с деталями расхода или None если не найден
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM expenses WHERE id = ? AND is_cancelled = 0
        """, (expense_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Получаем долги по этому расходу
        cursor.execute("""
            SELECT 
                debtor_username,
                creditor_username,
                amount,
                paid_amount,
                (amount - paid_amount) as remaining
            FROM debts
            WHERE expense_id = ?
        """, (expense_id,))
        
        debts = []
        for debt_row in cursor.fetchall():
            debts.append({
                'debtor': debt_row['debtor_username'],
                'creditor': debt_row['creditor_username'],
                'amount': debt_row['amount'],
                'paid': debt_row['paid_amount'],
                'remaining': debt_row['remaining']
            })
        
        created_at_str = row['created_at']
        try:
            created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            except:
                created_at = datetime.now()
        
        conn.close()
        
        return {
            'id': row['id'],
            'description': row['description'],
            'total_amount': row['total_amount'],
            'creator_username': row['creator_username'],
            'created_at': created_at,
            'debts': debts
        }
    
    def get_expense_by_description(self, description: str, creator_username: Optional[str] = None) -> Optional[Dict]:
        """
        Найти расход по описанию
        
        Args:
            description: Описание расхода
            creator_username: Если указан, искать только расходы этого пользователя
        
        Returns:
            Детали расхода или None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if creator_username:
            cursor.execute("""
                SELECT id FROM expenses 
                WHERE description = ? AND creator_username = ? AND is_cancelled = 0
                ORDER BY created_at DESC
                LIMIT 1
            """, (description, creator_username))
        else:
            cursor.execute("""
                SELECT id FROM expenses 
                WHERE description = ? AND is_cancelled = 0
                ORDER BY created_at DESC
                LIMIT 1
            """, (description,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self.get_expense_details(row['id'])
        return None
    
    def cancel_expense(self, expense_id: int, username: str) -> bool:
        """
        Отменить расход
        
        Args:
            expense_id: ID расхода
            username: Кто отменяет (должен быть создателем)
        
        Returns:
            True если успешно, False если нет прав или расход не найден
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Проверяем что расход существует и пользователь - создатель
        cursor.execute("""
            SELECT creator_username FROM expenses 
            WHERE id = ? AND is_cancelled = 0
        """, (expense_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        
        if row['creator_username'] != username:
            conn.close()
            return False
        
        # Помечаем расход как отменённый
        cursor.execute("""
            UPDATE expenses SET is_cancelled = 1 WHERE id = ?
        """, (expense_id,))
        
        # Удаляем все долги по этому расходу
        cursor.execute("""
            DELETE FROM debts WHERE expense_id = ?
        """, (expense_id,))
        
        # Получаем описание для истории
        cursor.execute("""
            SELECT description FROM expenses WHERE id = ?
        """, (expense_id,))
        expense_row = cursor.fetchone()
        description = expense_row['description'] if expense_row else 'расход'
        
        # Записываем в историю
        cursor.execute("""
            INSERT INTO operation_history (expense_id, operation_type, username, description)
            VALUES (?, ?, ?, ?)
        """, (expense_id, 'expense_cancelled', username, f"Отменён расход '{description}'"))
        
        conn.commit()
        conn.close()
        return True
    
    def get_debts_grouped_by_expense(self) -> Dict[str, List[Dict]]:
        """
        Получить долги сгруппированные по расходам
        
        Returns:
            Словарь где ключ - описание расхода, значение - список долгов
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                e.description,
                d.debtor_username,
                d.creditor_username,
                d.amount,
                d.paid_amount,
                (d.amount - d.paid_amount) as remaining
            FROM debts d
            JOIN expenses e ON d.expense_id = e.id
            WHERE (d.amount - d.paid_amount) > 0 AND e.is_cancelled = 0
            ORDER BY e.created_at DESC, e.description
        """)
        
        grouped = {}
        for row in cursor.fetchall():
            description = row['description']
            if description not in grouped:
                grouped[description] = []
            
            grouped[description].append({
                'debtor': row['debtor_username'],
                'creditor': row['creditor_username'],
                'amount': row['amount'],
                'paid': row['paid_amount'],
                'remaining': row['remaining']
            })
        
        conn.close()
        return grouped
    
    def get_debt_amount(self, debtor_username: str, creditor_username: str) -> float:
        """Получить сумму долга между двумя пользователями"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT SUM(amount - paid_amount) as total
            FROM debts
            WHERE debtor_username = ? AND creditor_username = ?
            AND (amount - paid_amount) > 0
        """, (debtor_username, creditor_username))
        
        result = cursor.fetchone()
        conn.close()
        
        return result['total'] or 0.0

