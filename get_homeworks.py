import mysql.connector
from db import db
def get_homeworks():
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        query = "SELECT id, name, type, deadline FROM homework"
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            return {"status": False, "res": []}

        homework_list = []
        for row in results:
            homework_list.append({
                "id": row["id"],
                "name": row["name"],
                "type": row["type"],
                "deadline": row["deadline"]
            })

        return {"status": True, "res": homework_list}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": []}

    finally:
        connection.close()

