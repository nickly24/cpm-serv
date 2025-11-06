#!/usr/bin/env python3
"""
Скрипт для добавления поля visible: false ко всем документам в коллекции tests
"""

import pymongo
from pymongo.errors import ConnectionFailure
from datetime import datetime

# Строка подключения к новой MongoDB
MONGODB_URI = 'mongodb://gen_user:I_OBNu~9oHF0(m@81.200.148.71:27017/default_db?authSource=admin&directConnection=true'

def print_status(message, status="INFO"):
    """Вывод статуса с временной меткой"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_symbol = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️"
    }.get(status, "ℹ️")
    print(f"[{timestamp}] {status_symbol} {message}")

def main():
    """Основная функция"""
    print_status("=" * 60, "INFO")
    print_status("Добавление поля visible: false в коллекцию tests", "INFO")
    print_status("=" * 60, "INFO")
    
    client = None
    
    try:
        # Подключение к MongoDB
        print_status("Подключение к MongoDB...", "INFO")
        client = pymongo.MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000
        )
        
        # Проверка подключения
        try:
            client.admin.command('ping')
            print_status("Подключение успешно", "SUCCESS")
        except ConnectionFailure as e:
            print_status(f"Ошибка подключения: {str(e)}", "ERROR")
            return
        
        db = client.default_db
        tests_collection = db.tests
        
        # Получаем общее количество документов
        total_count = tests_collection.count_documents({})
        print_status(f"Всего документов в коллекции tests: {total_count}", "INFO")
        
        if total_count == 0:
            print_status("Коллекция tests пуста", "WARNING")
            return
        
        # Находим документы, у которых нет поля visible или оно не равно false
        # Обновляем только те документы, у которых нет поля visible
        result = tests_collection.update_many(
            {"visible": {"$exists": False}},
            {"$set": {"visible": False}}
        )
        
        modified_count = result.modified_count
        
        print_status("=" * 60, "INFO")
        print_status(f"Обработано документов: {modified_count}", "SUCCESS")
        print_status(f"Всего документов в коллекции: {total_count}", "INFO")
        
        # Проверяем, сколько документов теперь имеют visible: false
        visible_false_count = tests_collection.count_documents({"visible": False})
        print_status(f"Документов с visible: false: {visible_false_count}", "INFO")
        
        # Проверяем, есть ли документы без поля visible
        without_visible = tests_collection.count_documents({"visible": {"$exists": False}})
        if without_visible > 0:
            print_status(f"ВНИМАНИЕ: Осталось {without_visible} документов без поля visible", "WARNING")
        
        print_status("=" * 60, "INFO")
        print_status("ОПЕРАЦИЯ ЗАВЕРШЕНА", "SUCCESS")
        print_status("=" * 60, "INFO")
        
    except KeyboardInterrupt:
        print_status("\nОперация прервана пользователем", "WARNING")
    except Exception as e:
        print_status(f"Критическая ошибка: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
    finally:
        # Закрываем соединение
        if client:
            client.close()
            print_status("Соединение закрыто", "INFO")

if __name__ == '__main__':
    main()

