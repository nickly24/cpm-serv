import mysql.connector
from db import db
def get_student_homework_dashboard(student_id):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        # Получаем все домашние задания
        cursor.execute("SELECT id, name, type, deadline FROM homework")
        homeworks = cursor.fetchall()

        if not homeworks:
            return {"status": False, "res": []}

        result_list = []

        for hw in homeworks:
            # Ищем, есть ли запись в homework_sessions для этого студента и этой домашки
            cursor.execute("""
                SELECT status, result 
                FROM homework_sessions 
                WHERE student_id = %s AND homework_id = %s
            """, (student_id, hw["id"]))
            session = cursor.fetchone()

            if not session:
                homework_status = "ДЗ не сделано"
                score = None
            else:
                if session["status"] == 1:
                    homework_status = "ДЗ сдано"
                    score = session["result"]
                else:
                    homework_status = "ДЗ не сделано"
                    score = None

            result_list.append({
                "homework_id": hw["id"],
                "homework_name": hw["name"],
                "homework_type": hw["type"],
                "deadline": hw["deadline"],
                "status": homework_status,
                "result": score
            })

        return {"status": True, "res": result_list}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "res": []}

    finally:
        connection.close()



