#!/usr/bin/env python3
"""
Скрипт для миграции данных из одной MongoDB в другую
Переносит все коллекции, документы и индексы
"""

import pymongo
from pymongo.errors import ConnectionFailure, OperationFailure
from datetime import datetime
import sys

# Строки подключения
SOURCE_URI = 'mongodb://gen_user:77tanufe@109.73.202.73:27017/default_db?authSource=admin&directConnection=true'
TARGET_URI = 'mongodb://gen_user:I_OBNu~9oHF0(m@81.200.148.71:27017/default_db?authSource=admin&directConnection=true'

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

def test_connection(client, name):
    """Проверка подключения к БД"""
    try:
        client.admin.command('ping')
        print_status(f"Подключение к {name} успешно", "SUCCESS")
        return True
    except ConnectionFailure as e:
        print_status(f"Ошибка подключения к {name}: {str(e)}", "ERROR")
        return False
    except Exception as e:
        print_status(f"Неожиданная ошибка при подключении к {name}: {str(e)}", "ERROR")
        return False

def get_collections(db):
    """Получить список всех коллекций в БД"""
    try:
        collections = db.list_collection_names()
        # Исключаем системные коллекции
        collections = [c for c in collections if not c.startswith('system.')]
        return collections
    except Exception as e:
        print_status(f"Ошибка при получении списка коллекций: {str(e)}", "ERROR")
        return []

def copy_collection(source_collection, target_collection, collection_name):
    """Копировать коллекцию из источника в цель"""
    try:
        # Получаем количество документов
        doc_count = source_collection.count_documents({})
        print_status(f"Коллекция '{collection_name}': найдено {doc_count} документов", "INFO")
        
        if doc_count == 0:
            print_status(f"Коллекция '{collection_name}' пуста, пропускаем", "WARNING")
            return {"copied": 0, "errors": 0}
        
        # Копируем документы батчами
        batch_size = 1000
        copied = 0
        errors = 0
        
        cursor = source_collection.find().batch_size(batch_size)
        batch = []
        
        for doc in cursor:
            batch.append(doc)
            
            if len(batch) >= batch_size:
                try:
                    target_collection.insert_many(batch, ordered=False)
                    copied += len(batch)
                    print_status(f"Коллекция '{collection_name}': скопировано {copied}/{doc_count} документов", "INFO")
                    batch = []
                except Exception as e:
                    errors += len(batch)
                    print_status(f"Ошибка при копировании батча в '{collection_name}': {str(e)}", "ERROR")
                    batch = []
        
        # Копируем оставшиеся документы
        if batch:
            try:
                target_collection.insert_many(batch, ordered=False)
                copied += len(batch)
            except Exception as e:
                errors += len(batch)
                print_status(f"Ошибка при копировании последнего батча в '{collection_name}': {str(e)}", "ERROR")
        
        print_status(f"Коллекция '{collection_name}': скопировано {copied} документов, ошибок: {errors}", 
                    "SUCCESS" if errors == 0 else "WARNING")
        
        return {"copied": copied, "errors": errors}
        
    except Exception as e:
        print_status(f"Критическая ошибка при копировании коллекции '{collection_name}': {str(e)}", "ERROR")
        return {"copied": 0, "errors": 1}

def copy_indexes(source_collection, target_collection, collection_name):
    """Копировать индексы из исходной коллекции в целевую"""
    try:
        indexes = source_collection.list_indexes()
        index_count = 0
        
        for index in indexes:
            # Пропускаем индекс по умолчанию _id
            if index['name'] == '_id_':
                continue
            
            try:
                # Создаем индекс
                keys = index['key']
                options = {k: v for k, v in index.items() if k not in ['key', 'v', 'ns']}
                
                target_collection.create_index(
                    list(keys.items()),
                    **options
                )
                index_count += 1
                print_status(f"Коллекция '{collection_name}': создан индекс '{index['name']}'", "INFO")
            except Exception as e:
                # Игнорируем ошибку, если индекс уже существует
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    print_status(f"Ошибка при создании индекса '{index['name']}' в '{collection_name}': {str(e)}", "WARNING")
        
        if index_count > 0:
            print_status(f"Коллекция '{collection_name}': создано {index_count} индексов", "SUCCESS")
        
        return index_count
        
    except Exception as e:
        print_status(f"Ошибка при копировании индексов для '{collection_name}': {str(e)}", "WARNING")
        return 0

def main():
    """Основная функция миграции"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Миграция данных MongoDB')
    parser.add_argument('--yes', '-y', action='store_true', 
                       help='Автоматически подтверждать все запросы (пропускать непустые коллекции)')
    args = parser.parse_args()
    
    print_status("=" * 60, "INFO")
    print_status("Начало миграции MongoDB", "INFO")
    print_status("=" * 60, "INFO")
    print_status(f"Источник: {SOURCE_URI.split('@')[1].split('/')[0]}", "INFO")
    print_status(f"Цель: {TARGET_URI.split('@')[1].split('/')[0]}", "INFO")
    print_status("=" * 60, "INFO")
    
    source_client = None
    target_client = None
    
    try:
        # Подключение к исходной БД
        print_status("Подключение к исходной БД...", "INFO")
        source_client = pymongo.MongoClient(
            SOURCE_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000
        )
        
        if not test_connection(source_client, "исходной БД"):
            sys.exit(1)
        
        source_db = source_client.default_db
        
        # Подключение к целевой БД
        print_status("Подключение к целевой БД...", "INFO")
        target_client = pymongo.MongoClient(
            TARGET_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000
        )
        
        if not test_connection(target_client, "целевой БД"):
            sys.exit(1)
        
        target_db = target_client.default_db
        
        # Получаем список коллекций
        print_status("Получение списка коллекций...", "INFO")
        collections = get_collections(source_db)
        
        if not collections:
            print_status("Не найдено коллекций для миграции", "WARNING")
            sys.exit(0)
        
        print_status(f"Найдено коллекций: {len(collections)}", "INFO")
        print_status(f"Коллекции: {', '.join(collections)}", "INFO")
        print_status("=" * 60, "INFO")
        
        # Статистика
        total_docs = 0
        total_errors = 0
        total_indexes = 0
        
        # Миграция каждой коллекции
        for i, collection_name in enumerate(collections, 1):
            print_status(f"[{i}/{len(collections)}] Обработка коллекции '{collection_name}'...", "INFO")
            
            source_collection = source_db[collection_name]
            target_collection = target_db[collection_name]
            
            # Проверяем, не пуста ли целевая коллекция
            target_count = target_collection.count_documents({})
            if target_count > 0:
                if not args.yes:
                    response = input(f"⚠️  Коллекция '{collection_name}' в целевой БД уже содержит {target_count} документов. Продолжить? (y/n): ")
                    if response.lower() != 'y':
                        print_status(f"Пропущена коллекция '{collection_name}'", "WARNING")
                        continue
                else:
                    print_status(f"Коллекция '{collection_name}' в целевой БД уже содержит {target_count} документов, пропускаем", "WARNING")
                    continue
            
            # Копируем документы
            result = copy_collection(source_collection, target_collection, collection_name)
            total_docs += result["copied"]
            total_errors += result["errors"]
            
            # Копируем индексы
            indexes_count = copy_indexes(source_collection, target_collection, collection_name)
            total_indexes += indexes_count
            
            print_status("-" * 60, "INFO")
        
        # Итоговая статистика
        print_status("=" * 60, "INFO")
        print_status("МИГРАЦИЯ ЗАВЕРШЕНА", "SUCCESS")
        print_status("=" * 60, "INFO")
        print_status(f"Обработано коллекций: {len(collections)}", "INFO")
        print_status(f"Скопировано документов: {total_docs}", "SUCCESS" if total_errors == 0 else "WARNING")
        print_status(f"Ошибок при копировании: {total_errors}", "ERROR" if total_errors > 0 else "SUCCESS")
        print_status(f"Создано индексов: {total_indexes}", "INFO")
        print_status("=" * 60, "INFO")
        
    except KeyboardInterrupt:
        print_status("\nМиграция прервана пользователем", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"Критическая ошибка: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Закрываем соединения
        if source_client:
            source_client.close()
            print_status("Соединение с исходной БД закрыто", "INFO")
        if target_client:
            target_client.close()
            print_status("Соединение с целевой БД закрыто", "INFO")

if __name__ == '__main__':
    main()

