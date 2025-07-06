import mysql.connector
from db import db
def assign_proctor_to_group(proctor_id, group_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor()

    try:
        # Проверим существует ли группа
        cursor.execute('''SELECT id FROM `groups` WHERE id = %s''', (group_id,))
        group = cursor.fetchone()
        if not group:
            print("Группа не найдена")
            return {"status": False, "error": "Group not found"}

        # Проверим существует ли проктор
        cursor.execute("SELECT id FROM proctors WHERE id = %s", (proctor_id,))
        proctor = cursor.fetchone()
        if not proctor:
            return {"status": False, "error": "Proctor not found"}

        # Обновляем группу у проктора
        update_query = "UPDATE proctors SET group_id = %s WHERE id = %s"
        cursor.execute(update_query, (group_id, proctor_id))
        connection.commit()

        return {"status": True}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "error": str(err)}

    finally:
        connection.close()
