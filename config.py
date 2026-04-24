# config.py
import os

# Секретный ключ для сессий
SECRET_KEY = 'pgsql_security_2024_7f8e2a9d4c1b5f3e8a2d6c9b1e4f7a2d'

# База данных приложения (Windows)
APP_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'exam_system',
    'user': 'app_user',
    'password': 'app_password'
}

# Тестовая среда (Ubuntu)
TEST_DB_CONFIG = {
    'host': '192.168.1.239',  # IP вашей Ubuntu
    'port': 5432,
    'database': 'exam_test_db',
    'user': 'test_user',
    'password': 'test_password'
}