"""
Пул подключений к MySQL для cpm-serv.
Ограничивает число одновременных соединений и переиспользует их под нагрузкой.
"""
import mysql.connector
from mysql.connector import pooling
from db import db

# Размер пула: при 400 пользователях не создаём 400 соединений,
# а берём из пула (макс pool_size). Остальные запросы ждут в очереди.
POOL_SIZE = 25
POOL_NAME = "cpm_serv_pool"

_connection_pool = None


def _get_pool():
    """Создаёт или возвращает существующий пул соединений."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = pooling.MySQLConnectionPool(
            pool_name=POOL_NAME,
            pool_size=POOL_SIZE,
            pool_reset_session=True,
            host=db.host,
            port=db.port,
            user=db.user,
            password=db.password,
            database=db.db,
            autocommit=False,
        )
    return _connection_pool


def get_db_connection():
    """
    Берёт соединение из пула (не создаёт новое каждый раз).
    После использования обязательно вызывать close_db_connection(connection).
    """
    pool = _get_pool()
    return pool.get_connection()


def close_db_connection(connection):
    """
    Возвращает соединение в пул (connection.close() в пуле не разрывает сокет,
    а возвращает объект в пул для переиспользования).
    """
    if connection:
        try:
            if connection.is_connected():
                connection.rollback()  # сброс незакоммиченной транзакции перед возвратом в пул
        except Exception:
            pass
        try:
            connection.close()
        except Exception:
            pass
