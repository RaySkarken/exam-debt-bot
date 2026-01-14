"""
REST API для веб-приложения
Роль: Разработчик - создание API endpoints
"""
from flask import Blueprint, jsonify, request
from src.database import Database

api_bp = Blueprint('api', __name__)
db = Database()


@api_bp.route('/debts', methods=['GET'])
def get_debts():
    """Получить список всех долгов"""
    creditor = request.args.get('creditor')
    debtor = request.args.get('debtor')
    
    debts = db.get_debts(creditor_username=creditor) if creditor else db.get_debts()
    
    if debtor:
        debts = [d for d in debts if d['debtor'] == debtor]
    
    return jsonify({
        'success': True,
        'debts': debts,
        'count': len(debts)
    })


@api_bp.route('/expenses', methods=['GET'])
def get_expenses():
    """Получить список расходов"""
    # Получаем все расходы через долги
    debts = db.get_debts()
    expenses_dict = {}
    
    for debt in debts:
        expense_id = debt.get('id')  # Это ID долга, нужно получить expense_id
        description = debt.get('description', 'расход')
        if description not in expenses_dict:
            expenses_dict[description] = {
                'description': description,
                'total_amount': 0,
                'debts': []
            }
        expenses_dict[description]['debts'].append(debt)
        expenses_dict[description]['total_amount'] += debt.get('amount', 0)
    
    expenses = list(expenses_dict.values())
    
    return jsonify({
        'success': True,
        'expenses': expenses,
        'count': len(expenses)
    })


@api_bp.route('/expenses', methods=['POST'])
def create_expense():
    """Создать новый расход"""
    data = request.get_json()
    
    description = data.get('description')
    amount = data.get('amount')
    creator = data.get('creator')
    participants = data.get('participants', [])
    
    if not all([description, amount, creator, participants]):
        return jsonify({
            'success': False,
            'error': 'Не все поля заполнены'
        }), 400
    
    try:
        amount = float(amount)
        expense_id = db.create_expense(
            description=description,
            total_amount=amount,
            creator_username=creator,
            participants=participants
        )
        
        return jsonify({
            'success': True,
            'expense_id': expense_id,
            'message': 'Расход создан'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/payments', methods=['POST'])
def create_payment():
    """Выплатить долг"""
    data = request.get_json()
    
    debtor = data.get('debtor')
    creditor = data.get('creditor')
    amount = data.get('amount')
    
    if not all([debtor, creditor, amount]):
        return jsonify({
            'success': False,
            'error': 'Не все поля заполнены'
        }), 400
    
    try:
        amount = float(amount)
        success = db.pay_debt(debtor, creditor, amount)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Выплата принята'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Ошибка при выплате долга'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Получить статистику"""
    username = request.args.get('username')
    
    stats = db.get_statistics(username=username)
    
    return jsonify({
        'success': True,
        'statistics': stats
    })


@api_bp.route('/history', methods=['GET'])
def get_history():
    """Получить историю операций"""
    limit = request.args.get('limit', 50, type=int)
    expense_id = request.args.get('expense_id', type=int)
    
    history = db.get_operation_history(expense_id=expense_id, limit=limit)
    
    # Конвертируем datetime в строки для JSON
    for op in history:
        op['created_at'] = op['created_at'].isoformat()
    
    return jsonify({
        'success': True,
        'history': history,
        'count': len(history)
    })


@api_bp.route('/debts/grouped', methods=['GET'])
def get_grouped_debts():
    """Получить долги сгруппированные по расходам"""
    grouped = db.get_debts_grouped_by_expense()
    
    # Конвертируем в список для JSON
    result = []
    for description, debts in grouped.items():
        result.append({
            'description': description,
            'debts': debts
        })
    
    return jsonify({
        'success': True,
        'grouped': result,
        'count': len(result)
    })

