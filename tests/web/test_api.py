"""
Тесты для REST API веб-приложения
Роль: Тестировщик
"""
import pytest
import json
import os
import tempfile
from src.web.app import app
from src.database import Database


@pytest.fixture
def client():
    """Фикстура для тестового клиента Flask"""
    # Создаём временную БД для тестов
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Заменяем БД в app на тестовую
    with app.app_context():
        from src.web.api import db
        db.db_path = path
        db.init_db()
    
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    
    # Удаляем тестовую БД
    os.unlink(path)


def test_get_debts_empty(client):
    """Тест получения пустого списка долгов"""
    response = client.get('/api/debts')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['count'] == 0


def test_create_expense(client):
    """Тест создания расхода"""
    expense_data = {
        'description': 'пицца',
        'amount': 4200,
        'creator': 'Вася',
        'participants': ['Петя', 'Маша']
    }
    
    response = client.post(
        '/api/expenses',
        data=json.dumps(expense_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'expense_id' in data


def test_get_debts_after_expense(client):
    """Тест получения долгов после создания расхода"""
    # Создаём расход
    expense_data = {
        'description': 'обед',
        'amount': 1000,
        'creator': 'Вася',
        'participants': ['Петя']
    }
    client.post(
        '/api/expenses',
        data=json.dumps(expense_data),
        content_type='application/json'
    )
    
    # Получаем долги
    response = client.get('/api/debts')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['count'] > 0


def test_create_payment(client):
    """Тест выплаты долга"""
    # Создаём расход
    expense_data = {
        'description': 'кофе',
        'amount': 500,
        'creator': 'Вася',
        'participants': ['Петя']
    }
    client.post(
        '/api/expenses',
        data=json.dumps(expense_data),
        content_type='application/json'
    )
    
    # Выплачиваем долг
    payment_data = {
        'debtor': 'Петя',
        'creditor': 'Вася',
        'amount': 500
    }
    
    response = client.post(
        '/api/payments',
        data=json.dumps(payment_data),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True


def test_get_statistics(client):
    """Тест получения статистики"""
    response = client.get('/api/statistics')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'statistics' in data


def test_get_history(client):
    """Тест получения истории"""
    response = client.get('/api/history')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'history' in data

