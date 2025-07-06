import mysql.connector
from db import db
def reset_group_for_user(user_type, user_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor()

    try:
        if user_type == "student":
            query = "UPDATE students SET group_id = NULL WHERE id = %s"
        elif user_type == "proctor":
            query = "UPDATE proctors SET group_id = NULL WHERE id = %s"
        else:
            print("Неверный тип пользователя")
            return {"status": False}

        cursor.execute(query, (user_id,))
        connection.commit()

        if cursor.rowcount == 0:
            return {"status": False}

        return {"status": True}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False}

    finally:
        connection.close()
