"""
Общие фикстуры для тестов
"""
import pytest
from src.database import Database
import os
import tempfile


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


