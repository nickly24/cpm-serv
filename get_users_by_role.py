import mysql.connector
from db import db

def get_users_by_role(role):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.db
    )
    cursor = connection.cursor(dictionary=True)

    try:
        if role == "student":
            cursor.execute("SELECT id, full_name FROM students ORDER BY full_name")
        elif role == "proctor":
            cursor.execute("SELECT id, full_name FROM proctors ORDER BY full_name")
        elif role == "examinator":
            cursor.execute("SELECT id, full_name FROM examinators ORDER BY full_name")
        elif role == "supervisor":
            cursor.execute("SELECT id, full_name FROM supervisors ORDER BY full_name")
        else:
            return {"status": False, "error": "Invalid role provided."}

        result = [{"id": row["id"], "full_name": row["full_name"]} for row in cursor.fetchall()]
        return {"status": True, "res": result}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": [], "error": str(err)}

    finally:
        connection.close()
