import mysql.connector
from db import db

def validate_student_by_tg_name(tg_name):
    """
    Проверяет существование студента по Telegram никнейму и возвращает его данные включая логин и пароль
    
    Args:
        tg_name (str): Telegram никнейм студента
    
    Returns:
        dict: Результат проверки с данными студента (ФИО, класс, группа, логин, пароль), если найден
    """
    connection = None
    cursor = None
    
    try:
        if not tg_name or tg_name.strip() == "":
            return {
                "status": False,
                "error": "Telegram никнейм не может быть пустым"
            }
        
        # Подключаемся к базе данных
        connection = mysql.connector.connect(
            host=db.host,
            port=db.port,
            user=db.user,
            password=db.password,
            db=db.db
        )
        cursor = connection.cursor(dictionary=True)
        
        # Ищем студента по tg_name с получением логина и пароля из auth_users
        query = """
        SELECT s.id, s.full_name, s.class, s.group_id, s.tg_name, 
               a.username as login, a.password
        FROM students s
        LEFT JOIN auth_users a ON s.id = a.ref_id AND a.role = 'student'
        WHERE s.tg_name = %s
        """
        cursor.execute(query, (tg_name,))
        student = cursor.fetchone()
        
        if not student:
            return {
                "status": False,
                "message": "Студент с таким Telegram никнеймом не найден"
            }
        
        return {
            "status": True,
            "message": "Студент найден",
            "student_data": {
                "student_id": student['id'],
                "full_name": student['full_name'],
                "class": student['class'],
                "group_id": student['group_id'],
                "tg_name": student['tg_name'],
                "login": student['login'],
                "password": student['password']
            }
        }
        
    except mysql.connector.Error as e:
        return {
            "status": False,
            "error": f"Ошибка базы данных: {str(e)}"
        }
        
    except Exception as e:
        return {
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

