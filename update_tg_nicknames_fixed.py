#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import mysql.connector
from db import db

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
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Пробуем разные варианты поиска
        search_queries = [
            # Точное совпадение полного имени
            ("SELECT * FROM students WHERE full_name = %s", [full_name]),
            # Поиск по ФАМИЛИЯ + ИМЯ (начало строки) - это основной поиск!
            ("SELECT * FROM students WHERE full_name LIKE %s", [f"{last_name} {first_name}%"]),
            # Поиск по ФАМИЛИЯ + ИМЯ + что угодно после
            ("SELECT * FROM students WHERE full_name LIKE %s", [f"{last_name} {first_name} %"]),
            # Поиск по сокращенному имени (только фамилия + имя)
            ("SELECT * FROM students WHERE full_name = %s", [f"{last_name} {first_name}"]),
            # Поиск по имени + фамилии (оба должны быть в строке)
            ("SELECT * FROM students WHERE full_name LIKE %s AND full_name LIKE %s", [f"%{first_name}%", f"%{last_name}%"]),
            # Поиск без учета пробелов
            ("SELECT * FROM students WHERE REPLACE(full_name, ' ', '') = REPLACE(%s, ' ', '')", [full_name])
        ]
        
        for query, params in search_queries:
            try:
                cursor.execute(query, params)
                student = cursor.fetchone()
                if student:
                    return student
            except Exception as e:
                print(f"Ошибка в запросе {query}: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"Ошибка в find_student_by_name: {e}")
        return None
    finally:
        if cursor:
            cursor.close()

def update_student_tg_name(connection, student_id, tg_name):
    """
    Обновляет Telegram никнейм студента
    """
    cursor = None
    try:
        cursor = connection.cursor()
        query = "UPDATE students SET tg_name = %s WHERE id = %s"
        cursor.execute(query, (tg_name, student_id))
        connection.commit()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении студента {student_id}: {e}")
        connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()

def main():
    """
    Основная функция
    """
    try:
        # Читаем Excel файл
        df = pd.read_excel('__pycache__/Список сборной + ТГ.xlsx')
        
        print("Структура Excel файла:")
        print(f"Количество строк: {len(df)}")
        print(f"Количество колонок: {len(df.columns)}")
        print(f"Названия колонок: {list(df.columns)}")
        print()
        
        # Подключаемся к базе данных
        connection = get_db_connection()
        
        print(f"Начинаем обработку {len(df)} записей...")
        print("=" * 80)
        
        updated_count = 0
        not_found_count = 0
        error_count = 0
        skipped_count = 0
        
        for index, row in df.iterrows():
            try:
                # Получаем данные из строки
                last_name = str(row['Фамилия']).strip()
                first_name = str(row['Имя']).strip()
                middle_name = str(row['Отчество']).strip()
                tg_name = row['Аккаунт участника в ТГ']
                
                # Пропускаем если нет Telegram никнейма
                if pd.isna(tg_name) or str(tg_name).strip() == "":
                    print(f"Строка {index + 1}: Пропущено - нет Telegram никнейма")
                    skipped_count += 1
                    continue
                
                # Очищаем Telegram никнейм
                clean_tg = clean_telegram_username(tg_name)
                
                if clean_tg == "":
                    print(f"Строка {index + 1}: Пропущено - пустой Telegram никнейм")
                    skipped_count += 1
                    continue
                
                # Формируем полное имя
                full_name = f"{last_name} {first_name} {middle_name}".strip()
                
                print(f"Обрабатываем: {full_name} -> {clean_tg}")
                
                # Ищем студента в базе данных
                student = find_student_by_name(connection, full_name, first_name, last_name)
                
                if student:
                    # Обновляем Telegram никнейм
                    if update_student_tg_name(connection, student['id'], clean_tg):
                        print(f"  ✓ Обновлен студент ID {student['id']}: {student['full_name']}")
                        updated_count += 1
                    else:
                        print(f"  ✗ Ошибка при обновлении студента {student['id']}")
                        error_count += 1
                else:
                    print(f"  ✗ Студент не найден: {full_name}")
                    not_found_count += 1
                    
            except Exception as e:
                print(f"Ошибка в строке {index + 1}: {e}")
                error_count += 1
                continue
        
        connection.close()
        
        print("=" * 80)
        print("РЕЗУЛЬТАТЫ ОБРАБОТКИ:")
        print(f"✓ Успешно обновлено: {updated_count}")
        print(f"✗ Не найдено в базе: {not_found_count}")
        print(f"✗ Ошибки: {error_count}")
        print(f"⏭ Пропущено (нет Telegram): {skipped_count}")
        print(f"📊 Всего обработано: {len(df)}")
        print()
        
        # Получаем финальную статистику
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM students")
        total_students = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as with_tg FROM students WHERE tg_name IS NOT NULL AND tg_name != ''")
        with_tg = cursor.fetchone()['with_tg']
        
        cursor.close()
        connection.close()
        
        print("=" * 80)
        print("ФИНАЛЬНАЯ СТАТИСТИКА:")
        print(f"Всего студентов в базе: {total_students}")
        print(f"С Telegram никнеймами: {with_tg}")
        print(f"Без Telegram никнеймов: {total_students - with_tg}")
        print(f"Покрытие: {(with_tg / total_students * 100):.1f}%")
        
    except Exception as e:
        print(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
