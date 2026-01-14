// JavaScript для веб-приложения управления долгами
// Роль: Разработчик - фронтенд логика

const API_BASE = '/api';

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDebts();
});

// Управление вкладками
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Убираем активный класс со всех вкладок и контента
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    // Активируем выбранную вкладку
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Загружаем данные для вкладки
    switch(tabName) {
        case 'debts':
            loadDebts();
            break;
        case 'expenses':
            loadExpenses();
            break;
        case 'statistics':
            loadStatistics();
            break;
        case 'history':
            loadHistory();
            break;
    }
}

// Загрузка долгов
async function loadDebts() {
    const container = document.getElementById('debts-list');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/debts`);
        const data = await response.json();
        
        if (data.success && data.debts.length > 0) {
            container.innerHTML = data.debts.map(debt => `
                <div class="debt-card">
                    <div class="debt-card-header">
                        <h3>${debt.debtor} → ${debt.creditor}</h3>
                        <span class="debt-amount">${Math.round(debt.remaining)}₽</span>
                    </div>
                    <div class="debt-info">
                        <p>📦 ${debt.description}</p>
                        <p>💸 Долг: ${Math.round(debt.amount)}₽ | Выплачено: ${Math.round(debt.paid)}₽</p>
                    </div>
                    <button class="btn btn-success" onclick="showPaymentForm('${debt.debtor}', '${debt.creditor}', ${debt.remaining})">
                        💸 Выплатить
                    </button>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>🎉 Нет активных долгов!</h3>
                    <p>Все долги погашены</p>
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><h3>❌ Ошибка загрузки</h3><p>${error.message}</p></div>`;
    }
}

// Загрузка расходов
async function loadExpenses() {
    const container = document.getElementById('expenses-list');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/expenses`);
        const data = await response.json();
        
        if (data.success && data.expenses.length > 0) {
            container.innerHTML = data.expenses.map(expense => `
                <div class="expense-card">
                    <h3>📦 ${expense.description}</h3>
                    <p>💰 Сумма: ${Math.round(expense.total_amount)}₽</p>
                    <p>👥 Долгов: ${expense.debts.length}</p>
                </div>
            `).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📦 Нет расходов</h3>
                    <p>Создайте первый расход</p>
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><h3>❌ Ошибка загрузки</h3><p>${error.message}</p></div>`;
    }
}

// Загрузка статистики
async function loadStatistics() {
    const container = document.getElementById('statistics-content');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/statistics`);
        const data = await response.json();
        
        if (data.success) {
            const stats = data.statistics;
            container.innerHTML = `
                <div class="statistics-grid">
                    <div class="stat-card">
                        <h3>${stats.debt_count || 0}</h3>
                        <p>Активных долгов</p>
                    </div>
                    <div class="stat-card">
                        <h3>${Math.round(stats.total_debt || 0)}₽</h3>
                        <p>Общая сумма</p>
                    </div>
                    ${stats.debtors_count ? `
                    <div class="stat-card">
                        <h3>${stats.debtors_count}</h3>
                        <p>Должников</p>
                    </div>
                    ` : ''}
                    ${stats.creditors_count ? `
                    <div class="stat-card">
                        <h3>${stats.creditors_count}</h3>
                        <p>Кредиторов</p>
                    </div>
                    ` : ''}
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><h3>❌ Ошибка загрузки</h3><p>${error.message}</p></div>`;
    }
}

// Загрузка истории
async function loadHistory() {
    const container = document.getElementById('history-list');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/history?limit=20`);
        const data = await response.json();
        
        if (data.success && data.history.length > 0) {
            container.innerHTML = data.history.map(op => {
                const date = new Date(op.created_at);
                const dateStr = date.toLocaleString('ru-RU');
                return `
                    <div class="history-item">
                        <div>
                            <strong>${op.username}</strong>
                            <p>${op.description}</p>
                        </div>
                        <span class="history-date">${dateStr}</span>
                    </div>
                `;
            }).join('');
        } else {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📜 История пуста</h3>
                    <p>Операций пока нет</p>
                </div>
            `;
        }
    } catch (error) {
        container.innerHTML = `<div class="empty-state"><h3>❌ Ошибка загрузки</h3><p>${error.message}</p></div>`;
    }
}

// Показать форму создания расхода
function showCreateExpenseForm() {
    document.getElementById('expense-modal').style.display = 'block';
}

// Создать расход
async function createExpense(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        description: formData.get('description'),
        amount: parseFloat(formData.get('amount')),
        creator: formData.get('creator'),
        participants: formData.get('participants').split(',').map(p => p.trim())
    };
    
    try {
        const response = await fetch(`${API_BASE}/expenses`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Расход создан!');
            closeModal();
            form.reset();
            loadExpenses();
            loadDebts();
            loadStatistics();
        } else {
            alert(`❌ Ошибка: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Ошибка: ${error.message}`);
    }
}

// Показать форму выплаты
function showPaymentForm(debtor, creditor, amount) {
    document.getElementById('payment-debtor').value = debtor;
    document.getElementById('payment-creditor').value = creditor;
    document.getElementById('payment-debtor-display').value = debtor;
    document.getElementById('payment-creditor-display').value = creditor;
    document.getElementById('payment-amount').value = Math.round(amount);
    document.getElementById('payment-amount').max = amount;
    document.getElementById('payment-modal').style.display = 'block';
}

// Создать выплату
async function createPayment(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const data = {
        debtor: formData.get('debtor'),
        creditor: formData.get('creditor'),
        amount: parseFloat(formData.get('amount'))
    };
    
    try {
        const response = await fetch(`${API_BASE}/payments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Выплата принята!');
            closeModal();
            form.reset();
            loadDebts();
            loadStatistics();
            loadHistory();
        } else {
            alert(`❌ Ошибка: ${result.error}`);
        }
    } catch (error) {
        alert(`❌ Ошибка: ${error.message}`);
    }
}

// Закрыть модальное окно
function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

