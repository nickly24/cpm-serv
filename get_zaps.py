import mysql.connector
from db import db

def get_zaps_by_student(student_id):
    """
    Получает все запросы на отгул студента
    
    Args:
        student_id: ID студента
    
    Returns:
        dict: Список запросов
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
            SELECT 
                id,
                student_id,
                text,
                status,
                answer
            FROM zaps
            WHERE student_id = %s
            ORDER BY id DESC
        """, (student_id,))

        zaps = cursor.fetchall()

        return {
            "status": True,
            "zaps": zaps
        }

    except mysql.connector.Error as err:
        return {"status": False, "error": str(err)}

    finally:
        connection.close()

def get_all_zaps(status=None):
    """
    Получает все запросы на отгул (для админов)
    
    Args:
        status: Фильтр по статусу ('set', 'apr', 'dec')
    
    Returns:
        dict: Список запросов с информацией о студентах
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
        query = """
            SELECT 
                z.id,
                z.student_id,
                z.text,
                z.status,
                z.answer,
                s.full_name
            FROM zaps z
            JOIN students s ON z.student_id = s.id
        """
        
        params = []
        if status:
            query += " WHERE z.status = %s"
            params.append(status)
        
        query += " ORDER BY z.id DESC"

        cursor.execute(query, tuple(params))
        zaps = cursor.fetchall()

        return {
            "status": True,
            "zaps": zaps
        }

    except mysql.connector.Error as err:
        return {"status": False, "error": str(err)}

    finally:
        connection.close()

def get_zap_by_id(zap_id):
    """
    Получает запрос на отгул по ID
    
    Args:
        zap_id: ID запроса
    
    Returns:
        dict: Информация о запросе с изображениями
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
        # Получаем информацию о запросе
        cursor.execute("""
            SELECT 
                z.id,
                z.student_id,
                z.text,
                z.status,
                z.answer,
                s.full_name
            FROM zaps z
            JOIN students s ON z.student_id = s.id
            WHERE z.id = %s
        """, (zap_id,))

        zap = cursor.fetchone()
        
        if not zap:
            return {"status": False, "error": "Запрос не найден"}

        # Получаем изображения
        cursor.execute("SELECT id, img FROM zap_img WHERE zap_id = %s", (zap_id,))
        images = cursor.fetchall()

        return {
            "status": True,
            "zap": zap,
            "images": images
        }

    except mysql.connector.Error as err:
        return {"status": False, "error": str(err)}

    finally:
        connection.close()

