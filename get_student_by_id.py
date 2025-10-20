import mysql.connector
from db import db

def get_student_by_id(student_id):
    """
    Получает информацию о студенте по ID
    
    Args:
        student_id (str): ID студента
    
    Returns:
        dict: Информация о студенте
    """
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.db
    )
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, full_name, group_id, class, tg_name 
            FROM students 
            WHERE id = %s
        """, (student_id,))
        
        student = cursor.fetchone()
        
        if not student:
            return {"status": False, "error": "Студент не найден"}
        
        result = {
            "id": student["id"],
            "name": student["full_name"],
            "class": student["class"],
            "group_id": student["group_id"],
            "tg_name": student["tg_name"]
        }
        
        return {"status": True, "data": result}

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        return {"status": False, "error": str(err)}

    finally:
        connection.close()
