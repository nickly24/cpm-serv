import mysql.connector
from db import db
def get_unassigned_students_and_proctors():
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)
    try:
        # Студенты без группы
        cursor.execute("SELECT id, full_name FROM students WHERE group_id IS NULL")
        students = cursor.fetchall()
        unassigned_students = [{"student_id": s["id"], "full_name": s["full_name"]} for s in students]

        # Прокторы без группы
        cursor.execute("SELECT id, full_name FROM proctors WHERE group_id IS NULL")
        proctors = cursor.fetchall()
        unassigned_proctors = [{"proctor_id": p["id"], "full_name": p["full_name"]} for p in proctors]

        return {
            "status": True,
            "unassigned_students": unassigned_students,
            "unassigned_proctors": unassigned_proctors
        }

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "unassigned_students": [], "unassigned_proctors": []}

    finally:
        connection.close()