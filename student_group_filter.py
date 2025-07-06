import mysql.connector
from db import db
def get_student_ids_and_names_by_group(group_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = "SELECT id, full_name FROM students WHERE group_id = %s"
        cursor.execute(query, (group_id,))
        results = cursor.fetchall()

        if not results:
            return {"status": False, "res": []}

        data = [{"id": row['id'], "full_name": row['full_name']} for row in results]
        return {"status": True, "res": data}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": []}

    finally:
        connection.close()
