"""
Общие фикстуры для тестов
"""
import pytest
from src.database import Database
import os
import tempfile

# Настройка Playwright для E2E тестов
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@pytest.fixture(scope="function")
def db():
    """Фикстура для создания временной БД для тестов"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    database = Database(db_path=path)
    yield database
    os.unlink(path)


@pytest.fixture(scope="function")
def context():
    """Фикстура для хранения контекста между шагами"""
    return {}


@pytest.fixture(scope="session")
def browser():
    """Фикстура для браузера Playwright"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright не установлен")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


