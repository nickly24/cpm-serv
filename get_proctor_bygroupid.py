import mysql.connector
from db import db
def get_proctor_by_group(group_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT id, full_name FROM proctors WHERE group_id = %s", (group_id,))
        proctor = cursor.fetchone()

        if not proctor:
            return {"status": False, "res": 'No proctor in this group'}

        return {
            "status": True,
            "res": {
                "proctor_id": proctor["id"],
                "full_name": proctor["full_name"]
            }
        }

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": None}

    finally:
        connection.close()
