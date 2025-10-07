import mysql.connector
from db import db
import random
import string

def add_student(full_name, class_number):
    """
    Добавляет нового студента с автоматической генерацией логина и пароля
    
    Args:
        full_name (str): Полное имя студента
        class_number (int): Класс студента (9, 10 или 11)
    
    Returns:
        dict: Результат операции с данными студента
    """
    connection = None
    cursor = None
    
    try:
        # Проверяем корректность класса
        if class_number not in [9, 10, 11]:
            return {
                "status": False,
                "error": "Класс должен быть 9, 10 или 11"
            }
        
        # Подключаемся к базе данных
        connection = mysql.connector.connect(
            host=db.host,
            port=db.port,
            user=db.user,
            password=db.password,
            db=db.db
        )
        cursor = connection.cursor()
        
        # Генерируем логин на основе имени и класса
        # Формат: первая буква имени + фамилия + класс + случайные цифры
        name_parts = full_name.strip().split()
        if len(name_parts) < 2:
            return {
                "status": False,
                "error": "Необходимо указать имя и фамилию"
            }
        
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower()
        
        # Генерируем уникальный логин
        base_login = f"{first_name[0]}{last_name}{class_number}"
        login = base_login
        
        # Проверяем уникальность логина и добавляем цифры если нужно
        counter = 1
        while True:
            cursor.execute("SELECT 1 FROM auth_users WHERE username = %s", (login,))
            if not cursor.fetchone():
                break
            login = f"{base_login}{counter}"
            counter += 1
        
        # Генерируем пароль (8 символов: буквы + цифры)
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # 1. Добавляем студента в таблицу students
        insert_student_query = """
        INSERT INTO students (full_name, class, group_id) 
        VALUES (%s, %s, NULL)
        """
        cursor.execute(insert_student_query, (full_name, class_number))
        student_id = cursor.lastrowid
        
        # 2. Добавляем запись в auth_users
        insert_auth_query = """
        INSERT INTO auth_users (username, password, ref_id, role) 
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_auth_query, (login, password, student_id, 'student'))
        
        # Подтверждаем транзакцию
        connection.commit()
        
        return {
            "status": True,
            "message": "Студент успешно добавлен",
            "student_data": {
                "student_id": student_id,
                "full_name": full_name,
                "class": class_number,
                "login": login,
                "password": password,
                "group_id": None
            }
        }
        
    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        return {
            "status": False,
            "error": f"Ошибка базы данных: {str(e)}"
        }
        
    except Exception as e:
        if connection:
            connection.rollback()
        return {
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
