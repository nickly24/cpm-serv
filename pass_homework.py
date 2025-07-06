import mysql.connector
import datetime
from db import db
def pass_homework(session_id, date_pass):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        # 1. Получаем homework_id по session_id
        cursor.execute("SELECT homework_id FROM homework_sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        
        if not session:
            print("Сессия не найдена.")
            return {"status": False}

        homework_id = session["homework_id"]

        # 2. Получаем deadline из homework
        cursor.execute("SELECT deadline FROM homework WHERE id = %s", (homework_id,))
        homework = cursor.fetchone()

        if not homework:
            print("Домашняя работа не найдена.")
            return {"status": False}

        deadline = homework["deadline"]

        # 3. Считаем просрочку
        result = 100
        if date_pass > deadline:
            delta_days = (date_pass - deadline).days
            result -= delta_days * 5
            if result < 0:
                result = 0

        # 4. Обновляем homework_session
        update_query = """
            UPDATE homework_sessions 
            SET status = 1, result = %s, date_pass = %s 
            WHERE id = %s
        """
        cursor.execute(update_query, (result, date_pass, session_id))
        connection.commit()

        print(f"Оценка выставлена: {result} баллов")
        return {"status": True, "result": result}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        connection.rollback()
        return {"status": False}

    finally:
        connection.close()


