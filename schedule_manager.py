import pymongo
from datetime import datetime
from typing import List, Dict, Optional

class ScheduleManager:
    def __init__(self):
        self.client = pymongo.MongoClient(
            'mongodb://gen_user:77tanufe@109.73.202.73:27017/default_db?authSource=admin&directConnection=true',
            serverSelectionTimeoutMS=5000,  # 5 секунд таймаут
            connectTimeoutMS=5000,         # 5 секунд на подключение
            socketTimeoutMS=5000,          # 5 секунд на операции
            maxPoolSize=10,                # Максимум 10 соединений
            retryWrites=True
        )
        self.db = self.client.default_db
        self.collection = self.db.schedule
    
    def get_all_schedule(self) -> Dict:
        """Получить все занятия из расписания"""
        try:
            # Проверяем подключение к MongoDB
            self.client.admin.command('ping')
            # Получаем все занятия без сложной агрегации
            schedule = list(self.collection.find())
            
            # Конвертируем ObjectId в строки для JSON сериализации
            for lesson in schedule:
                if '_id' in lesson:
                    lesson['_id'] = str(lesson['_id'])
            
            return {
                "status": True,
                "message": "Расписание успешно загружено",
                "schedule": schedule
            }
            
        except Exception as e:
            return {
                "status": False,
                "error": f"Ошибка при загрузке расписания: {str(e)}"
            }
    
    def add_lesson(self, lesson_data: Dict) -> Dict:
        """Добавить новое занятие"""
        try:
            # Проверяем подключение к MongoDB
            self.client.admin.command('ping')
            # Валидация данных
            required_fields = ['day_of_week', 'start_time', 'end_time', 'lesson_name', 'teacher_name', 'location']
            for field in required_fields:
                if not lesson_data.get(field):
                    return {
                        "status": False,
                        "error": f"Поле '{field}' обязательно для заполнения"
                    }
            
            # Проверяем корректность дня недели
            valid_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            if lesson_data['day_of_week'] not in valid_days:
                return {
                    "status": False,
                    "error": "Некорректный день недели. Используйте: Понедельник, Вторник, Среда, Четверг, Пятница, Суббота, Воскресенье"
                }
            
            # Проверяем, что время окончания больше времени начала
            if lesson_data['start_time'] >= lesson_data['end_time']:
                return {
                    "status": False,
                    "error": "Время окончания должно быть больше времени начала"
                }
            
            # Проверяем пересечения с существующими занятиями
            existing_lesson = self.collection.find_one({
                "day_of_week": lesson_data['day_of_week'],
                "$or": [
                    {
                        "start_time": {"$lt": lesson_data['end_time']},
                        "end_time": {"$gt": lesson_data['start_time']}
                    }
                ]
            })
            
            if existing_lesson:
                return {
                    "status": False,
                    "error": f"Занятие пересекается с существующим: {existing_lesson['lesson_name']} ({existing_lesson['start_time']}-{existing_lesson['end_time']})"
                }
            
            # Добавляем метаданные
            lesson_data['created_at'] = datetime.now()
            lesson_data['updated_at'] = datetime.now()
            
            result = self.collection.insert_one(lesson_data)
            
            return {
                "status": True,
                "message": "Занятие успешно добавлено",
                "lesson_id": str(result.inserted_id)
            }
            
        except Exception as e:
            return {
                "status": False,
                "error": f"Ошибка при добавлении занятия: {str(e)}"
            }
    
    def edit_lesson(self, lesson_id: str, lesson_data: Dict) -> Dict:
        """Редактировать занятие"""
        try:
            # Проверяем подключение к MongoDB
            self.client.admin.command('ping')
            from bson import ObjectId
            
            # Проверяем существование занятия
            if not ObjectId.is_valid(lesson_id):
                return {
                    "status": False,
                    "error": "Некорректный ID занятия"
                }
            
            existing_lesson = self.collection.find_one({"_id": ObjectId(lesson_id)})
            if not existing_lesson:
                return {
                    "status": False,
                    "error": "Занятие не найдено"
                }
            
            # Валидация данных
            required_fields = ['day_of_week', 'start_time', 'end_time', 'lesson_name', 'teacher_name', 'location']
            for field in required_fields:
                if not lesson_data.get(field):
                    return {
                        "status": False,
                        "error": f"Поле '{field}' обязательно для заполнения"
                    }
            
            # Проверяем корректность дня недели
            valid_days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
            if lesson_data['day_of_week'] not in valid_days:
                return {
                    "status": False,
                    "error": "Некорректный день недели"
                }
            
            # Проверяем, что время окончания больше времени начала
            if lesson_data['start_time'] >= lesson_data['end_time']:
                return {
                    "status": False,
                    "error": "Время окончания должно быть больше времени начала"
                }
            
            # Проверяем пересечения с другими занятиями (исключая текущее)
            conflicting_lesson = self.collection.find_one({
                "_id": {"$ne": ObjectId(lesson_id)},
                "day_of_week": lesson_data['day_of_week'],
                "$or": [
                    {
                        "start_time": {"$lt": lesson_data['end_time']},
                        "end_time": {"$gt": lesson_data['start_time']}
                    }
                ]
            })
            
            if conflicting_lesson:
                return {
                    "status": False,
                    "error": f"Занятие пересекается с существующим: {conflicting_lesson['lesson_name']} ({conflicting_lesson['start_time']}-{conflicting_lesson['end_time']})"
                }
            
            # Обновляем данные
            lesson_data['updated_at'] = datetime.now()
            
            result = self.collection.update_one(
                {"_id": ObjectId(lesson_id)},
                {"$set": lesson_data}
            )
            
            if result.modified_count > 0:
                return {
                    "status": True,
                    "message": "Занятие успешно обновлено"
                }
            else:
                return {
                    "status": False,
                    "error": "Не удалось обновить занятие"
                }
                
        except Exception as e:
            return {
                "status": False,
                "error": f"Ошибка при редактировании занятия: {str(e)}"
            }
    
    def delete_lesson(self, lesson_id: str) -> Dict:
        """Удалить занятие"""
        try:
            # Проверяем подключение к MongoDB
            self.client.admin.command('ping')
            from bson import ObjectId
            
            if not ObjectId.is_valid(lesson_id):
                return {
                    "status": False,
                    "error": "Некорректный ID занятия"
                }
            
            result = self.collection.delete_one({"_id": ObjectId(lesson_id)})
            
            if result.deleted_count > 0:
                return {
                    "status": True,
                    "message": "Занятие успешно удалено"
                }
            else:
                return {
                    "status": False,
                    "error": "Занятие не найдено"
                }
                
        except Exception as e:
            return {
                "status": False,
                "error": f"Ошибка при удалении занятия: {str(e)}"
            }
    
    def close_connection(self):
        """Закрыть соединение с базой данных"""
        self.client.close()

