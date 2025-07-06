import mysql.connector
from db import db
def get_proctor_homework_sessions(proctor_id, homework_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        # 1. Получаем group_id проектора
        cursor.execute("SELECT group_id FROM proctors WHERE id = %s", (proctor_id,))
        proctor = cursor.fetchone()

        if not proctor or proctor["group_id"] is None:
            return {"status": False, "res": []}

        group_id = proctor["group_id"]

        # 2. Получаем студентов в этой группе
        cursor.execute("SELECT id, full_name FROM students WHERE group_id = %s", (group_id,))
        students = cursor.fetchall()

        if not students:
            return {"status": False, "res": []}

        student_dict = {student["id"]: student["full_name"] for student in students}
        student_ids = list(student_dict.keys())

        # 3. Получаем homework_sessions по этим студентам и конкретной домашке
        format_strings = ','.join(['%s'] * len(student_ids))
        query = f"""
            SELECT * FROM homework_sessions 
            WHERE student_id IN ({format_strings}) AND homework_id = %s
        """
        cursor.execute(query, tuple(student_ids) + (homework_id,))
        sessions = cursor.fetchall()

        if not sessions:
            return {"status": False, "res": []}

        result_with_names = []
        for session in sessions:
            session_data = session.copy()
            session_data["student_full_name"] = student_dict.get(session["student_id"], "")
            result_with_names.append(session_data)

        return {"status": True, "res": result_with_names}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": []}

    finally:
        connection.close()

# === ПРИМЕР ===
if __name__ == "__main__":
    response = get_proctor_homework_sessions(1, 2)
    print(response)
