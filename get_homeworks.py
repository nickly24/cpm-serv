from db_pool import get_db_connection, close_db_connection

def get_homeworks():
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = "SELECT id, name, type, deadline FROM homework ORDER BY deadline DESC"
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

    except Exception as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": []}

    finally:
        if connection:
            close_db_connection(connection)