import pandas as pd
import mysql.connector
from db import db
import re

def read_excel_file(file_path):
    """
    Читает Excel файл и возвращает данные
    """
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path)
        
        print("Структура Excel файла:")
        print(f"Количество строк: {len(df)}")
        print(f"Количество колонок: {len(df.columns)}")
        print(f"Названия колонок: {list(df.columns)}")
        
        print("\nПервые 5 строк:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"Ошибка при чтении Excel файла: {e}")
        return None

def clean_telegram_username(tg_name):
    """
    Очищает Telegram никнейм от лишних символов
    """
    if pd.isna(tg_name) or tg_name == "":
        return ""
    
    # Преобразуем в строку
    tg_name = str(tg_name).strip()
    
    # Если это ссылка t.me, извлекаем username
    if 't.me/' in tg_name:
        tg_name = tg_name.split('t.me/')[-1]
    
    # Если это ссылка telegram.me, извлекаем username
    if 'telegram.me/' in tg_name:
        tg_name = tg_name.split('telegram.me/')[-1]
    
    # Если это ссылка tg.me, извлекаем username
    if 'tg.me/' in tg_name:
        tg_name = tg_name.split('tg.me/')[-1]
    
    # Убираем символ @ если есть
    if tg_name.startswith('@'):
        tg_name = tg_name[1:]
    
    # Убираем только пробелы в начале и конце, сохраняем подчеркивания и другие валидные символы
    tg_name = tg_name.strip()
    
    # Убираем параметры после ? если есть
    if '?' in tg_name:
        tg_name = tg_name.split('?')[0]
    
    return tg_name

def get_db_connection():
    """
    Создает подключение к базе данных
    """
    return mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        db=db.db
    )

def find_student_by_name(connection, full_name, first_name, last_name):
    """
    Ищет студента по имени в базе данных
    """
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Пробуем разные варианты поиска
        search_queries = [
            # Точное совпадение полного имени
            "SELECT * FROM students WHERE full_name = %s",
            # Поиск по имени + фамилии (начало строки)
            "SELECT * FROM students WHERE full_name LIKE %s",
            # Поиск по имени + фамилии (без учета порядка)
            "SELECT * FROM students WHERE full_name LIKE %s AND full_name LIKE %s",
            # Поиск без учета пробелов
            "SELECT * FROM students WHERE REPLACE(full_name, ' ', '') = REPLACE(%s, ' ', '')"
        ]
        
        # 1. Точное совпадение
        cursor.execute(search_queries[0], (full_name,))
        student = cursor.fetchone()
        if student:
            return student
        
        # 2. Поиск по началу строки (имя + фамилия)
        name_surname = f"{first_name} {last_name}"
        cursor.execute(search_queries[1], (f"{name_surname}%",))
        student = cursor.fetchone()
        if student:
            return student
        
        # 3. Поиск по имени + фамилии (оба должны быть в строке)
        if first_name and last_name:
            cursor.execute(search_queries[2], (f"%{first_name}%", f"%{last_name}%"))
            student = cursor.fetchone()
            if student:
                return student
        
        # 4. Поиск без учета пробелов
        cursor.execute(search_queries[3], (full_name,))
        student = cursor.fetchone()
        if student:
            return student
        
        return None
    finally:
        cursor.close()

def update_student_tg_name(connection, student_id, tg_name):
    """
    Обновляет Telegram никнейм студента
    """
    cursor = connection.cursor()
    
    try:
        query = "UPDATE students SET tg_name = %s WHERE id = %s"
        cursor.execute(query, (tg_name, student_id))
        connection.commit()
        
        return True
    except Exception as e:
        print(f"Ошибка при обновлении студента {student_id}: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def process_excel_data(file_path):
    """
    Обрабатывает данные из Excel файла и обновляет базу данных
    """
    # Читаем Excel файл
    df = read_excel_file(file_path)
    if df is None:
        return
    
    # Подключаемся к базе данных
    connection = get_db_connection()
    
    updated_count = 0
    not_found_count = 0
    error_count = 0
    
    print(f"\nНачинаем обработку {len(df)} записей...")
    print("=" * 80)
    
    for index, row in df.iterrows():
        try:
            # Извлекаем данные из колонок Excel файла
            last_name = row['Фамилия'] if 'Фамилия' in row else ""
            first_name = row['Имя'] if 'Имя' in row else ""
            middle_name = row['Отчество'] if 'Отчество' in row else ""
            tg_name = row['Аккаунт участника в ТГ'] if 'Аккаунт участника в ТГ' in row else ""
            
            # Формируем полное имя
            name_parts = []
            if last_name and str(last_name).strip():
                name_parts.append(str(last_name).strip())
            if first_name and str(first_name).strip():
                name_parts.append(str(first_name).strip())
            if middle_name and str(middle_name).strip():
                name_parts.append(str(middle_name).strip())
            
            full_name = " ".join(name_parts)
            
            if pd.isna(full_name):
                print(f"Строка {index + 1}: Пропущено - нет имени")
                continue
            
            # Очищаем Telegram никнейм
            clean_tg = clean_telegram_username(tg_name)
            
            if not clean_tg:
                print(f"Строка {index + 1}: Пропущено - нет Telegram никнейма")
                continue
            
            print(f"Обрабатываем: {full_name} -> {clean_tg}")
            
            # Ищем студента в базе
            student = find_student_by_name(connection, full_name, first_name, last_name)
            
            if student:
                # Обновляем Telegram никнейм
                if update_student_tg_name(connection, student['id'], clean_tg):
                    print(f"  ✓ Обновлен студент ID {student['id']}: {student['full_name']}")
                    updated_count += 1
                else:
                    print(f"  ✗ Ошибка при обновлении студента ID {student['id']}")
                    error_count += 1
            else:
                print(f"  ✗ Студент не найден: {full_name}")
                not_found_count += 1
                
        except Exception as e:
            print(f"Ошибка в строке {index + 1}: {e}")
            error_count += 1
    
    connection.close()
    
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
    print(f"✓ Успешно обновлено: {updated_count}")
    print(f"✗ Не найдено в базе: {not_found_count}")
    print(f"✗ Ошибки: {error_count}")
    print(f"Всего обработано: {updated_count + not_found_count + error_count}")

if __name__ == "__main__":
    file_path = "__pycache__/Список сборной + ТГ.xlsx"
    process_excel_data(file_path)
