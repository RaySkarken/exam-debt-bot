"""
E2E тесты для веб-интерфейса
Роль: Тестировщик - тестирование фронтенда
"""
import pytest
from playwright.sync_api import Page, expect
import os
import time

# URL веб-приложения для тестов
TEST_WEB_URL = os.getenv("TEST_WEB_URL", "http://localhost:5001")


@pytest.fixture(scope="module")
def web_url():
    """URL веб-приложения"""
    return TEST_WEB_URL


@pytest.fixture(scope="function")
def page(browser, web_url):
    """Создание новой страницы для каждого теста"""
    page = browser.new_page()
    page.goto(web_url)
    yield page
    page.close()


class TestWebInterface:
    """Тесты веб-интерфейса"""

    def test_page_loads(self, page: Page):
        """Тест: страница загружается"""
        expect(page).to_have_title("💰 Управление долгами")
        expect(page.locator("h1")).to_contain_text("💰 Управление долгами")

    def test_navigation_tabs(self, page: Page):
        """Тест: навигационные вкладки работают"""
        # Проверяем наличие всех вкладок
        expect(page.locator('button[data-tab="debts"]')).to_be_visible()
        expect(page.locator('button[data-tab="expenses"]')).to_be_visible()
        expect(page.locator('button[data-tab="statistics"]')).to_be_visible()
        expect(page.locator('button[data-tab="history"]')).to_be_visible()

        # Переключаемся на вкладку Расходы
        page.locator('button[data-tab="expenses"]').click()
        expect(page.locator("#expenses-tab")).to_have_class("tab-content active")

        # Переключаемся на вкладку Статистика
        page.locator('button[data-tab="statistics"]').click()
        expect(page.locator("#statistics-tab")).to_have_class("tab-content active")

        # Переключаемся на вкладку История
        page.locator('button[data-tab="history"]').click()
        expect(page.locator("#history-tab")).to_have_class("tab-content active")

        # Возвращаемся на вкладку Долги
        page.locator('button[data-tab="debts"]').click()
        expect(page.locator("#debts-tab")).to_have_class("tab-content active")

    def test_debts_section_loads(self, page: Page):
        """Тест: раздел долгов загружается"""
        # Ждём загрузки данных
        time.sleep(1)
        
        # Проверяем наличие секции долгов
        expect(page.locator("#debts-tab")).to_be_visible()
        expect(page.locator("#debts-list")).to_be_visible()

    def test_create_expense_modal(self, page: Page):
        """Тест: модальное окно создания расхода открывается"""
        # Переходим на вкладку Расходы
        page.locator('button[data-tab="expenses"]').click()
        expect(page.locator("#expenses-tab")).to_have_class("tab-content active")

        # Нажимаем кнопку создания расхода
        page.locator('button:has-text("➕ Создать расход")').click()

        # Проверяем, что модальное окно открылось
        expect(page.locator("#expense-modal")).to_be_visible()
        # В шаблоне заголовок модалки - h2
        expect(page.locator("#expense-modal h2")).to_contain_text("📝 Создать расход")

        # Проверяем наличие полей формы
        expect(page.locator('#expense-form input[name="description"]')).to_be_visible()
        expect(page.locator('#expense-form input[name="amount"]')).to_be_visible()
        expect(page.locator('#expense-form input[name="creator"]')).to_be_visible()
        expect(page.locator('#expense-form input[name="participants"]')).to_be_visible()

        # Закрываем модальное окно
        page.locator('#expense-modal button:has-text("Отмена")').click()
        expect(page.locator("#expense-modal")).not_to_be_visible()

    def test_create_expense_form(self, page: Page):
        """Тест: создание расхода через форму"""
        # Переходим на вкладку Расходы
        page.locator('button[data-tab="expenses"]').click()
        expect(page.locator("#expenses-tab")).to_have_class("tab-content active")

        # Открываем форму создания расхода
        page.locator('button:has-text("➕ Создать расход")').click()
        expect(page.locator("#expense-modal")).to_be_visible()

        # Заполняем форму
        page.locator('#expense-form input[name="description"]').fill("Тестовый расход")
        # На странице есть два input[name=amount] (расход + выплата), поэтому уточняем форму
        page.locator('#expense-form input[name="amount"]').fill("1000")
        page.locator('#expense-form input[name="creator"]').fill("Тестер")
        page.locator('#expense-form input[name="participants"]').fill("Тестер, Друг")

        # Отправляем форму
        page.locator('#expense-form button:has-text("✅ Создать")').click()

        # Проверяем, что форма закрылась
        expect(page.locator("#expense-modal")).not_to_be_visible()

    def test_refresh_buttons(self, page: Page):
        """Тест: кнопки обновления работают"""
        # Проверяем кнопку обновления в разделе долгов (должна быть видимой на активной вкладке)
        page.locator('button[data-tab="debts"]').click()
        expect(page.locator("#debts-tab")).to_have_class("tab-content active")
        page.locator('#debts-tab button:has-text("🔄 Обновить")').click()
        expect(page.locator("#debts-tab")).to_be_visible()

        # Переходим на вкладку Статистика
        page.locator('button[data-tab="statistics"]').click()
        expect(page.locator("#statistics-tab")).to_have_class("tab-content active")

        # Проверяем кнопку обновления статистики
        page.locator('#statistics-tab button:has-text("🔄 Обновить")').click()
        expect(page.locator("#statistics-tab")).to_be_visible()

    def test_api_endpoints(self, page: Page):
        """Тест: API endpoints отвечают"""
        # Проверяем /api/debts
        response = page.request.get(f"{TEST_WEB_URL}/api/debts")
        expect(response).to_be_ok()
        data = response.json()
        assert "debts" in data or "count" in data

        # Проверяем /api/statistics
        response = page.request.get(f"{TEST_WEB_URL}/api/statistics")
        expect(response).to_be_ok()
        data = response.json()
        assert "statistics" in data

        # Проверяем /api/history
        response = page.request.get(f"{TEST_WEB_URL}/api/history?limit=10")
        expect(response).to_be_ok()
        data = response.json()
        assert "history" in data or "count" in data

    def test_pay_debt_modal(self, page: Page):
        """Тест: модальное окно выплаты долга"""
        # Ждём загрузки долгов
        time.sleep(1)

        # Ищем кнопку выплаты долга
        pay_buttons = page.locator('button:has-text("💸 Выплатить")')
        if pay_buttons.count() > 0:
            # Нажимаем первую кнопку выплаты
            pay_buttons.first.click()
            time.sleep(0.5)

            # Проверяем, что модальное окно открылось
            expect(page.locator("#payment-modal")).to_be_visible()
            expect(page.locator("#payment-modal h2")).to_contain_text("💸 Выплата долга")

            # Закрываем модальное окно
            page.locator('#payment-modal button:has-text("Отмена")').click()
            time.sleep(0.5)
            expect(page.locator("#payment-modal")).not_to_be_visible()

