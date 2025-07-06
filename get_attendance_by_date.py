import mysql.connector
import datetime
from db import db
def get_attendance_by_date(date_str):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        # Преобразуем строку в дату (ожидаем формат YYYY-MM-DD)
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        # Получаем посещаемость на заданную дату с именами студентов
        query = """
            SELECT a.id, a.date, s.id AS student_id, s.full_name
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            WHERE a.date = %s
            ORDER BY s.full_name
        """
        cursor.execute(query, (date_obj,))
        attendance_records = cursor.fetchall()

        result = [
            {
                "attendance_id": record["id"],
                "student_id": record["student_id"],
                "full_name": record["full_name"],
                "date": record["date"].isoformat()
            }
            for record in attendance_records
        ]

        return {"status": True, "res": result}

    except ValueError:
        print("Неверный формат даты. Ожидается YYYY-MM-DD.")
        return {"status": False, "res": [], "error": "Invalid date format"}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": [], "error": str(err)}

    finally:
        connection.close()
