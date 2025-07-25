import mysql.connector
import datetime
from db import db
def create_homework_and_sessions(homework_name, homework_type, deadline_str):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor()

    try:
        # Преобразуем строку в дату
        # Ожидаем, что строка приходит в формате 'YYYY-MM-DD' (стандартный формат для HTML input type="date")
        deadline = datetime.datetime.strptime(deadline_str, "%Y-%m-%d").date()

        # Добавляем новую домашнюю работу в таблицу homework с дедлайном
        insert_homework_query = "INSERT INTO homework (name, type, deadline) VALUES (%s, %s, %s)"
        cursor.execute(insert_homework_query, (homework_name, homework_type, deadline))
        connection.commit()

        homework_id = cursor.lastrowid
        print(f"Домашняя работа добавлена с id: {homework_id}")

        # Получаем всех студентов
        cursor.execute("SELECT id FROM students")
        students = cursor.fetchall()

        if not students:
            print("Нет студентов для создания сессий.")
            return

        # Создаём записи в homework_sessions для каждого студента
        insert_session_query = """
            INSERT INTO homework_sessions (status, result, homework_id, student_id)
            VALUES (%s, %s, %s, %s)
        """
        for (student_id,) in students:
            cursor.execute(insert_session_query, (0, 0, homework_id, student_id))
        connection.commit()

        print(f"Созданы сессии для всех студентов.")

    except ValueError:
        print("Ошибка формата даты. Ожидается строка в формате YYYY-MM-DD.")
    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        connection.rollback()

    finally:
        connection.close()
        return {'status': True}