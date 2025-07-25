import mysql.connector
from db import db

def get_all_students():
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.db
    )
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, full_name, group_id, class FROM students ORDER BY full_name ASC")
        students = cursor.fetchall()

        result = [
            {
                "student_id": student["id"],
                "full_name": student["full_name"],
                "group_id": student["group_id"],
                "class": student["class"],
            }
            for student in students
        ]

        return {"status": True, "res": result}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": [], "error": str(err)}

    finally:
        connection.close()
