"""
Модуль для работы с JWT токенами и авторизацией
Использует PyJWT для создания и проверки токенов
Токены хранятся в HTTP-only cookies и не могут быть расшифрованы на клиенте
"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, make_response
import secrets

# Секретный ключ для подписи JWT токенов
# ВАЖНО: Должен совпадать с ключом на cpm-exam-main!
# В продакшене должен храниться в переменных окружения с одинаковым значением на обоих серверах
# Дефолтный ключ для разработки (одинаковый на обоих серверах)
DEFAULT_JWT_SECRET_KEY = "dev-secret-key-cpm-lms-2025-change-in-production"
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', DEFAULT_JWT_SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24  # Токен действителен 24 часа

# Роли пользователей
ROLES = {
    'admin': 'admin',
    'proctor': 'proctor',
    'student': 'student',
    'manager': 'manager',  # Для будущего использования
    'examinator': 'examinator',
    'supervisor': 'supervisor'
}


def generate_token(user_data):
    """
    Генерирует JWT токен для пользователя
    
    Args:
        user_data (dict): Словарь с данными пользователя:
            - role: роль пользователя
            - id: ID пользователя
            - full_name: полное имя
            - group_id: ID группы (опционально)
    
    Returns:
        str: JWT токен
    """
    # Создаем payload токена
    payload = {
        'role': user_data.get('role'),
        'id': user_data.get('id'),
        'full_name': user_data.get('full_name'),
        'group_id': user_data.get('group_id'),
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    
    # Генерируем токен
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    """
    Проверяет JWT токен и возвращает данные пользователя
    
    Args:
        token (str): JWT токен
    
    Returns:
        dict: Данные пользователя или None, если токен невалиден
    """
    try:
        # Декодируем токен
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return {
            'role': payload.get('role'),
            'id': payload.get('id'),
            'full_name': payload.get('full_name'),
            'group_id': payload.get('group_id')
        }
    except jwt.ExpiredSignatureError:
        return None  # Токен истек
    except jwt.InvalidTokenError:
        return None  # Невалидный токен


def get_token_from_request():
    """
    Получает JWT токен из заголовка Authorization или из HTTP-only cookie
    
    Returns:
        str: JWT токен или None
    """
    # Сначала пытаемся получить из заголовка Authorization
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '', 1)
    
    # Fallback на cookie для обратной совместимости
    return request.cookies.get('auth_token')


def get_current_user():
    """
    Получает текущего авторизованного пользователя из токена
    
    Returns:
        dict: Данные пользователя или None
    """
    token = get_token_from_request()
    if not token:
        return None
    return verify_token(token)


def require_auth(f):
    """
    Декоратор для проверки авторизации пользователя
    Проверяет наличие валидного JWT токена
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        
        if not user:
            return jsonify({
                'status': False,
                'error': 'Требуется авторизация'
            }), 401
        
        # Добавляем данные пользователя в kwargs для использования в роуте
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*allowed_roles):
    """
    Декоратор для проверки роли пользователя
    Пользователь должен иметь одну из указанных ролей
    
    Args:
        *allowed_roles: Список разрешенных ролей
    
    Example:
        @require_role('admin', 'proctor')
        def some_route():
            ...
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = kwargs.get('current_user')
            
            if not user or user.get('role') not in allowed_roles:
                return jsonify({
                    'status': False,
                    'error': 'Недостаточно прав доступа'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_self_or_role(user_id_param='student_id', *allowed_roles):
    """
    Декоратор для проверки доступа:
    - Пользователь может получить доступ к своим данным (проверка по ID)
    - Или пользователь должен иметь одну из указанных ролей
    
    Args:
        user_id_param: Название параметра с ID пользователя (может быть в URL или body)
        *allowed_roles: Список ролей, которые имеют доступ
    
    Example:
        @require_self_or_role('student_id', 'admin', 'proctor')
        def get_student_data(student_id):
            ...
        
        @app.route("/api/student/<student_id>")
        @require_self_or_role('student_id', 'admin', 'proctor')
        def get_student(student_id, current_user=None):
            ...
    """
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = kwargs.get('current_user')
            
            # Получаем ID из URL параметров или из body запроса
            requested_id = None
            
            # Проверяем URL параметры (в kwargs уже могут быть параметры из URL)
            # Нужно проверить разные варианты именования параметров
            param_variants = [
                user_id_param,
                user_id_param.replace('_id', 'Id'),  # student_id -> studentId
                user_id_param.replace('_id', 'ID'),  # student_id -> studentID
            ]
            
            for param in param_variants:
                if param in kwargs:
                    requested_id = kwargs[param]
                    break
            
            # Если не нашли в URL, проверяем body запроса
            if not requested_id:
                data = request.get_json() or {}
                for param in param_variants:
                    if param in data:
                        requested_id = data[param]
                        break
            
            # Если ID не найден, возвращаем ошибку
            if not requested_id:
                return jsonify({
                    'status': False,
                    'error': f'Параметр {user_id_param} не найден'
                }), 400
            
            # Преобразуем в int для сравнения
            try:
                requested_id = int(requested_id)
                user_id = int(user.get('id'))
            except (ValueError, TypeError):
                return jsonify({
                    'status': False,
                    'error': 'Неверный формат ID'
                }), 400
            
            # Проверяем доступ: либо это свои данные, либо есть нужная роль
            if user_id == requested_id or user.get('role') in allowed_roles:
                return f(*args, **kwargs)
            else:
                return jsonify({
                    'status': False,
                    'error': 'Недостаточно прав доступа'
                }), 403
        
        return decorated_function
    return decorator


def set_auth_cookie(response, token):
    """
    Устанавливает JWT токен в HTTP-only cookie
    
    Args:
        response: Flask response объект
        token: JWT токен
    
    Returns:
        response: Модифицированный response объект
    """
    # Определяем secure в зависимости от окружения
    is_production = os.environ.get('FLASK_ENV') != 'development'
    
    response.set_cookie(
        'auth_token',
        token,
        httponly=True,  # HTTP-only - недоступен из JavaScript
        secure=is_production,  # Только через HTTPS в продакшене
        samesite='Lax', # Защита от CSRF
        max_age=JWT_EXPIRATION_HOURS * 3600  # Время жизни cookie в секундах
    )
    return response


def clear_auth_cookie(response):
    """
    Удаляет JWT токен из cookie (для logout)
    
    Args:
        response: Flask response объект
    
    Returns:
        response: Модифицированный response объект
    """
    # Определяем secure в зависимости от окружения
    is_production = os.environ.get('FLASK_ENV') != 'development'
    
    response.set_cookie(
        'auth_token',
        '',
        httponly=True,
        secure=is_production,
        samesite='Lax',
        max_age=0  # Удаляем cookie
    )
    return response

