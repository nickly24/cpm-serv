import mysql.connector
from db import db
def delete_homework(homework_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor()

    try:
        # Удаляем все записи в homework_sessions для этого домашнего задания
        delete_sessions_query = "DELETE FROM homework_sessions WHERE homework_id = %s"
        cursor.execute(delete_sessions_query, (homework_id,))
        connection.commit()

        # Удаляем само домашнее задание
        delete_homework_query = "DELETE FROM homework WHERE id = %s"
        cursor.execute(delete_homework_query, (homework_id,))
        connection.commit()

        print(f"Домашнее задание с id {homework_id} успешно удалено вместе со всеми сессиями.")
        return {"status": True}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        connection.rollback()
        return {"status": False}

    finally:
        connection.close()