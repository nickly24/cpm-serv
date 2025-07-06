import mysql.connector
from db import db
import datetime

def add_attendance(student_id, date_str):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.db
    )
    cursor = connection.cursor()

    try:
        # Проверим существует ли студент
        cursor.execute("SELECT id FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"status": False, "error": "Student not found"}

        # Преобразуем строку в дату
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return {"status": False, "error": "Invalid date format (expected YYYY-MM-DD)"}

        # Проверим существует ли уже запись на эту дату для этого студента
        cursor.execute("SELECT id FROM attendance WHERE student_id = %s AND date = %s", (student_id, date_obj))
        existing = cursor.fetchone()
        if existing:
            return {"status": False, "error": "Attendance record already exists for this date"}

        # Добавляем запись в attendance
        insert_query = "INSERT INTO attendance (date, student_id) VALUES (%s, %s)"
        cursor.execute(insert_query, (date_obj, student_id))
        connection.commit()

        return {"status": True}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "error": str(err)}

    finally:
        connection.close()
