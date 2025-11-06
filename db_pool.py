"""
Модуль для управления подключениями к MySQL базе данных
Возвращает обычные подключения (без пула)
"""
import mysql.connector
from db import db


def get_db_connection():
    """
    Создает новое подключение к БД
    
    Returns:
        MySQLConnection: Подключение к БД
    """
    return mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        database=db.db
    )


def close_db_connection(connection):
    """
    Закрывает подключение к БД
    
    Args:
        connection: MySQLConnection объект для закрытия
    """
    if connection and connection.is_connected():
        connection.close()

