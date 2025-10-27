import mysql.connector
from db import db
from datetime import datetime

def create_zap(student_id, text, images=None):
    """
    Создает новый запрос на отгул от студента
    
    Args:
        student_id: ID студента
        text: Текст запроса
        images: Список словарей с blob данных и типом файла [{"data": blob, "type": "image/jpeg"}, ...]
    
    Returns:
        dict: Результат создания с zap_id
    """
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.db
    )
    cursor = connection.cursor()

    try:
        # Проверяем существование студента
        cursor.execute("SELECT id, full_name FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return {"status": False, "error": "Студент не найден"}

        # Создаем запись в таблице zaps
        cursor.execute(
            "INSERT INTO zaps (student_id, text, status) VALUES (%s, %s, 'set')",
            (student_id, text)
        )
        zap_id = cursor.lastrowid

        # Если есть изображения, сохраняем их с типом
        if images:
            for img_data in images:
                img_blob = img_data.get('data')
                img_type = img_data.get('type', 'image/jpeg')
                cursor.execute(
                    "INSERT INTO zap_img (zap_id, img, type) VALUES (%s, %s, %s)",
                    (zap_id, img_blob, img_type)
                )

        connection.commit()

        return {
            "status": True,
            "zap_id": zap_id,
            "message": "Запрос успешно создан"
        }

    except mysql.connector.Error as err:
        connection.rollback()
        return {"status": False, "error": str(err)}

    finally:
        connection.close()

