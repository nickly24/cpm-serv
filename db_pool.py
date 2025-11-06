"""
Модуль для управления пулом подключений к MySQL базе данных
Использует connection pooling для оптимизации производительности
"""
import mysql.connector
from mysql.connector import pooling
from db import db

# Глобальный пул подключений
_db_pool = None

def get_db_pool():
    """
    Получает или создает пул подключений к БД
    Использует singleton паттерн для единого пула на все приложение
    """
    global _db_pool
    
    if _db_pool is None:
        _db_pool = pooling.MySQLConnectionPool(
            pool_name="cpm_serv_pool",
            pool_size=20,  # Размер пула - 20 подключений
            pool_reset_session=True,  # Сбрасывать сессию при возврате в пул
            host=db.host,
            port=db.port,
            user=db.user,
            password=db.password,
            database=db.db,
            autocommit=False,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            connect_timeout=5,  # Таймаут подключения 5 секунд
            use_unicode=True
        )
    
    return _db_pool


def get_db_connection():
    """
    Получает подключение из пула
    ВАЖНО: После использования подключение должно быть возвращено в пул
    через метод close() или через context manager
    
    Returns:
        MySQLConnection: Подключение к БД из пула
        
    Raises:
        mysql.connector.PoolError: Если пул исчерпан или произошла ошибка
    """
    pool = get_db_pool()
    try:
        connection = pool.get_connection()
        return connection
    except pooling.PoolError as e:
        # Если пул исчерпан, логируем и пробуем еще раз
        print(f"Ошибка получения подключения из пула: {e}")
        raise


def close_db_connection(connection):
    """
    Возвращает подключение в пул
    Вместо закрытия подключения, возвращает его в пул для повторного использования
    
    Args:
        connection: MySQLConnection объект для возврата в пул
    """
    if connection and connection.is_connected():
        connection.close()  # Возвращает подключение в пул, а не закрывает его полностью

