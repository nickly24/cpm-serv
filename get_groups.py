import mysql.connector
from db import db
def get_all_groups():
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute('''SELECT id, name FROM `groups` ORDER BY name ASC''')
        groups = cursor.fetchall()

        if not groups:
            return {"status": False, "res": []}

        groups_list = [{"group_id": g["id"], "group_name": g["name"]} for g in groups]

        return {"status": True, "res": groups_list}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": []}

    finally:
        connection.close()

