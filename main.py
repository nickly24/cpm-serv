from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from auth import auth
from aun import aun
from jwt_auth import (
    generate_token, 
    require_auth, 
    require_role, 
    require_self_or_role,
    set_auth_cookie, 
    clear_auth_cookie,
    get_current_user
)
from student_group_filter import get_student_ids_and_names_by_group
from get_homeworks import get_homeworks
from get_homework_sessions_bygroupid import get_proctor_homework_sessions
import datetime
from pass_homework import pass_homework
from student_homework import get_student_homework_dashboard
from add_homework import create_homework_and_sessions
from delete_homework import delete_homework
from merge_groups_students_proctors import merge_groups_students_proctors
from get_unsigned_proctors_students import get_unassigned_students_and_proctors
from reset_groupid import reset_group_for_user
from change_proctor_group import assign_proctor_to_group
from change_student_group import assign_student_to_group
from get_groups import get_all_groups
from get_attendance_by_date import get_attendance_by_date
from get_attendance import get_attendance_diary
from add_attendance import add_attendance
from get_users_by_role import get_users_by_role
from delete_user import delete_user
from get_sessions import get_all_exams
from get_students import get_all_students
from get_student_by_id import get_student_by_id
from db_pool import get_db_connection, close_db_connection
from edit_homework_session import edit_homework_session
from add_student import add_student
from edit_student import edit_student
from validate_student_by_tg import validate_student_by_tg_name
from schedule_manager import ScheduleManager
from get_all_homework_results import get_all_homework_results
from get_homework_results_paginated import get_homework_results_paginated, get_homework_students
from get_ov_homework_table import get_ov_homework_table
from create_zap import create_zap
from get_zaps import get_zaps_by_student, get_all_zaps, get_zap_by_id
from process_zap import process_zap
import base64
import logging
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/*": {  # Обратите внимание на "/*" вместо "/api/*"
        "origins": [
            "https://cpm-lms.ru",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ],  # Только разрешенные домены
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,  # Важно для работы с cookies
        "expose_headers": ["Content-Type"]
    }
})

# Логирование всех запросов
@app.before_request
def log_request_info():
    """Логирует информацию о входящем запросе"""
    start_time = time.time()
    request.start_time = start_time
    
    # Получаем IP клиента
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
    
    # Логируем запрос
    logger.info(f"[CPM-SERV REQUEST] {request.method} {request.path} | IP: {client_ip} | Query: {dict(request.args)}")
    
    # Логируем тело запроса для POST/PUT (первые 500 символов)
    if request.method in ['POST', 'PUT'] and request.is_json:
        try:
            body = request.get_json()
            body_str = str(body)[:500]
            logger.info(f"[CPM-SERV REQUEST BODY] {body_str}")
        except:
            pass

@app.after_request
def log_response_info(response):
    """Логирует информацию об ответе"""
    # Вычисляем время выполнения
    if hasattr(request, 'start_time'):
        duration = (time.time() - request.start_time) * 1000  # в миллисекундах
    else:
        duration = 0
    
    # Логируем ответ
    logger.info(f"[CPM-SERV RESPONSE] {request.method} {request.path} | Status: {response.status_code} | Duration: {duration:.2f}ms")
    
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Логирует все исключения"""
    logger.error(f"[CPM-SERV ERROR] {request.method} {request.path} | Exception: {str(e)}", exc_info=True)
    return jsonify({"error": "Internal server error", "message": str(e)}), 500

@app.route("/")
def hello_world():
    """
    Обработчик для маршрута '/'.
    Возвращает JSON с приветствием.
    """
    return jsonify({"answer": "hello world!"})

@app.route("/api/auth", methods=['POST'])
def auth_route():
    """
    Авторизация пользователя
    Выдает JWT токен в HTTP-only cookie
    """
    data = request.get_json()
    body_login = data.get('login')
    body_password = data.get('password')
    
    if not body_login or not body_password:
        return jsonify({
            'status': False,
            'error': 'Логин и пароль обязательны'
        }), 400
    
    # Проверяем авторизацию
    answer = auth(body_login, body_password)
    
    # Если авторизация неуспешна
    if not answer.get('status') and not answer.get('sratus'):
        return jsonify({
            'status': False,
            'error': 'Неверный логин или пароль'
        }), 401
    
    # Получаем данные пользователя (исправляем опечатку 'sratus' -> 'status')
    user_data = answer.get('res', {})
    
    if not user_data:
        return jsonify({
            'status': False,
            'error': 'Ошибка получения данных пользователя'
        }), 500
    
    # Генерируем JWT токен
    token = generate_token(user_data)
    
    # Создаем response
    response = make_response(jsonify({
        'status': True,
        'message': 'Авторизация успешна',
        'user': user_data
    }))
    
    # Устанавливаем токен в HTTP-only cookie
    response = set_auth_cookie(response, token)
    
    return response

@app.route("/api/logout", methods=['POST'])
def logout_route():
    """
    Выход пользователя
    Удаляет JWT токен из cookie
    """
    response = make_response(jsonify({
        'status': True,
        'message': 'Выход выполнен успешно'
    }))
    
    # Удаляем токен из cookie
    response = clear_auth_cookie(response)
    
    return response


@app.route("/api/aun", methods=['POST'])
@require_auth
def aun_route(current_user=None):
    """
    Получение данных текущего авторизованного пользователя
    Теперь использует JWT токен из cookie
    """
    # Возвращаем данные текущего пользователя из токена
    return jsonify({
        'status': True,
        'role': current_user.get('role'),
        'entity_id': current_user.get('id'),
        'full_name': current_user.get('full_name'),
        'group_id': current_user.get('group_id')
    })

@app.route("/api/student-group-filter", methods=['POST'])
@require_role('admin', 'proctor')
def student_group_filter(current_user=None):
    data = request.get_json()
    id = data.get('id')
    answer = get_student_ids_and_names_by_group(id)
    return jsonify(answer)

@app.route("/api/get-homeworks")
def gethomeworks():
    return jsonify(get_homeworks())

@app.route("/api/get-homework-sessions", methods=['POST'])
@require_role('proctor')
def ghs(current_user=None):
    data = request.get_json()
    proctor_id = data.get('proctorId') 
    homework_id = data.get('homeworkId') 
    answer = get_proctor_homework_sessions(proctor_id, homework_id)
    return jsonify(answer)

@app.route("/api/pass_homework", methods=['POST'])
@require_role('proctor')
def pass_hw(current_user=None):
    """
    Оценивает домашнее задание
    Получает дату из HTTP запроса в формате YYYY-MM-DD и возвращает данные.
    """
    data = request.get_json()
    session_id = data.get('sessionId')
    date_pass = data.get('datePass')
    student_id = data.get('studentId')
    homework_id = data.get('homeworkId')

    if not date_pass:
        return jsonify({'error': 'Поле "datePass" отсутствует в запросе'}), 400

    try:
        date_object = datetime.date.fromisoformat(date_pass)
    except ValueError:
        try:
            # Попытка обработать дату в формате YYYY-M-DD (без лидирующего нуля)
            date_object = datetime.datetime.strptime(date_pass, '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({'error': f'Неверный формат даты: {str(e)}. Ожидается формат YYYY-MM-DD.'}), 400
    except Exception as e:
        return jsonify({'error': f'Произошла непредвиденная ошибка при обработке даты: {str(e)}'}), 500


    answer = pass_homework(session_id, date_object, student_id, homework_id)
    return jsonify(answer)


@app.route("/api/get-homeworks-student", methods=['POST'])
@require_self_or_role('studentId', 'proctor')
def ghst(current_user=None):
    data = request.get_json()
    student_id = data.get('studentId') 
    answer = get_student_homework_dashboard(student_id)
    return jsonify(answer)

@app.route("/api/get-all-homework-results", methods=['GET'])
@require_role('admin')
def get_all_hw_results(current_user=None):
    """
    Получить все домашние задания с результатами всех студентов
    Для админки - полная статистика по всем ДЗ
    """
    answer = get_all_homework_results()
    return jsonify(answer)

@app.route("/api/get-homework-results-paginated", methods=['POST'])
@require_role('admin')
def get_hw_results_paginated(current_user=None):
    """
    Получить домашние задания с пагинацией
    Оптимизированная версия для больших объемов данных
    """
    data = request.get_json() or {}
    
    page = data.get('page', 1)
    limit = data.get('limit', 10)
    filters = data.get('filters', {})
    
    # Валидация параметров
    try:
        page = int(page)
        limit = int(limit)
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:  # Максимум 100 заданий за раз
            limit = 10
    except (ValueError, TypeError):
        return jsonify({
            "status": False,
            "error": "Неверные параметры пагинации"
        }), 400
    
    answer = get_homework_results_paginated(page, limit, filters)
    return jsonify(answer)

@app.route("/api/get-homework-students", methods=['POST'])
@require_role('admin')
def get_hw_students(current_user=None):
    """
    Получить студентов для конкретного домашнего задания с пагинацией
    """
    data = request.get_json() or {}
    
    homework_id = data.get('homework_id')
    page = data.get('page', 1)
    limit = data.get('limit', 50)
    filters = data.get('filters', {})
    
    if not homework_id:
        return jsonify({
            "status": False,
            "error": "homework_id обязателен"
        }), 400
    
    # Валидация параметров
    try:
        homework_id = int(homework_id)
        page = int(page)
        limit = int(limit)
        if page < 1:
            page = 1
        if limit < 1 or limit > 200:  # Максимум 200 студентов за раз
            limit = 50
    except (ValueError, TypeError):
        return jsonify({
            "status": False,
            "error": "Неверные параметры"
        }), 400
    
    answer = get_homework_students(homework_id, page, limit, filters)
    return jsonify(answer)

@app.route("/api/edit-homework-session", methods=['POST'])
@require_role('admin', 'proctor')
def edit_hw_session(current_user=None):
    data = request.get_json()
    session_id = data.get('sessionId')
    result = data.get('result')
    date_pass = data.get('datePass')
    status = data.get('status')


    if not session_id:
        return jsonify({'error': 'Поле "sessionId" обязательно'}), 400

    answer = edit_homework_session(session_id=session_id, result=result, date_pass=date_pass, status=status)
    http_code = 200 if answer.get('status') else 400
    return jsonify(answer), http_code

@app.route("/api/create-homework", methods=['POST'])
@require_role('admin')
def create_hw(current_user=None):
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    name = data.get('homeworkName') 
    typee = data.get('homeworkType') 
    deadline_str = data.get('deadline') 
    answer = create_homework_and_sessions(name,typee,deadline_str)
    return jsonify(answer)
    
@app.route("/api/delete-homework", methods=['POST'])
@require_role('admin')
def delete_hw(current_user=None):
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    homework_id = data.get('homeworkId')
    answer = delete_homework(homework_id) 
    return jsonify(answer)

@app.route("/api/get-ov-homework-table", methods=['GET'])
@require_role('admin', 'supervisor', 'proctor')
def get_ov_homework_table_route(current_user=None):
    """
    Получает таблицу данных по домашним заданиям типа ОВ
    Доступен для администраторов и супервайзеров
    """
    answer = get_ov_homework_table()
    return jsonify(answer)

@app.route("/api/get-groups-students", methods=['GET'])
@require_role('admin')
def get_groups_students(current_user=None):
    answer = merge_groups_students_proctors()
    return jsonify(answer)

@app.route("/api/get-groups", methods=['GET'])
@require_role('admin')
def get_g(current_user=None):
    answer = get_all_groups()
    return jsonify(answer)

@app.route("/api/get-unsigned-proctors-students", methods=['GET'])
@require_role('admin')
def get_unsigned_p_s(current_user=None):
    answer = get_unassigned_students_and_proctors()
    return jsonify(answer)


@app.route("/api/remove-groupd-id-student", methods=['POST'])
@require_role('admin')
def remove_g_s(current_user=None):
    data = request.get_json()
    student_id = data.get('studentId')
    answer = reset_group_for_user('student', student_id)
    return jsonify(answer)


@app.route("/api/remove-groupd-id-proctor", methods=['POST'])
@require_role('admin')
def remove_g_p(current_user=None):
    data = request.get_json()
    proctor_id = data.get('proctorId')
    answer = reset_group_for_user('proctor', proctor_id)
    return jsonify(answer)


@app.route("/api/change-group-proctor", methods=['POST'])
@require_role('admin')
def change_p(current_user=None):
    data = request.get_json()
    proctor_id = data.get('proctorId')
    group_id = data.get('groupId')
    answer = assign_proctor_to_group(proctor_id, group_id)
    return jsonify(answer)


@app.route("/api/change-group-student", methods=['POST'])
@require_role('admin')
def change_s(current_user=None):
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id= data.get('studentId')
    group_id = data.get('groupId')
    print(group_id)
    answer = assign_student_to_group(student_id,group_id)
    return jsonify(answer)


@app.route("/api/get-attendance-by-date", methods=['POST'])
@require_role('admin')
def get_attendance_by_d(current_user=None):
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    date= data.get('date')
    answer = get_attendance_by_date(date)
    return jsonify(answer)


@app.route("/api/get-attendance-by-month", methods=['POST'])
@require_role('admin')
def get_attendance_by_m(current_user=None):
    data = request.get_json()
    month = data.get('month')
    year = data.get('year')
    answer = get_attendance_diary(year, month)
    return jsonify(answer)


@app.route("/api/add-attendance", methods=['POST'])
@require_role('admin')
def add_attendance_f(current_user=None):
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id= data.get('studentId')
    date= data.get('date')
    answer = add_attendance(student_id,date)
    return jsonify(answer)


@app.route("/api/get-users-by-role", methods=['POST'])
@require_role('admin')
def get_users_br(current_user=None):
    data = request.get_json()
    role = data.get('role')
    answer = get_users_by_role(role)
    return jsonify(answer)


@app.route("/api/delete-user", methods=['POST'])
@require_role('admin')
def del_us(current_user=None):
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    role= data.get('role')
    user_id= data.get('userId')
    answer = delete_user(role,user_id)
    return jsonify(answer)


@app.route("/api/get-students")
@require_role('admin')
def get_us(current_user=None):
    answer = get_all_students()
    return jsonify(answer)


@app.route("/api/get-class-name-by-studID", methods=['POST'])
@require_self_or_role('student_id', 'admin', 'proctor')
def get_class_name_by_stud_id(current_user=None):
    """
    Получает информацию о студенте по ID
    Ожидает JSON: {"student_id": "123"}
    """
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({"status": False, "error": "Отсутствует student_id"}), 400
        
        result = get_student_by_id(student_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500


@app.route("/api/add-student", methods=['POST'])
@require_role('admin')
def add_student_route(current_user=None):
    """
    Добавляет нового студента с автоматической генерацией логина и пароля
    
    Ожидаемые данные в JSON:
    {
        "full_name": "Имя Фамилия",
        "class": 9,  // или 10, или 11
        "tg_name": "@username"  // необязательно
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "status": False,
            "error": "Данные не предоставлены"
        }), 400
    
    full_name = data.get('full_name')
    class_number = data.get('class')
    tg_name = data.get('tg_name')
    
    if not full_name:
        return jsonify({
            "status": False,
            "error": "Поле 'full_name' обязательно"
        }), 400
    
    if not class_number:
        return jsonify({
            "status": False,
            "error": "Поле 'class' обязательно"
        }), 400
    
    try:
        class_number = int(class_number)
    except (ValueError, TypeError):
        return jsonify({
            "status": False,
            "error": "Поле 'class' должно быть числом"
        }), 400
    
    answer = add_student(full_name, class_number, tg_name)
    http_code = 200 if answer.get('status') else 400
    return jsonify(answer), http_code


@app.route("/api/edit-student", methods=['PUT'])
@require_role('admin')
def edit_student_route(current_user=None):
    """
    Редактирует данные студента
    
    Ожидаемые данные в JSON:
    {
        "student_id": 123,  // обязательно
        "full_name": "Новое Имя",  // необязательно
        "class": 10,  // необязательно
        "group_id": 5,  // необязательно
        "tg_name": "@new_username"  // необязательно
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "status": False,
            "error": "Данные не предоставлены"
        }), 400
    
    student_id = data.get('student_id')
    
    if not student_id:
        return jsonify({
            "status": False,
            "error": "Поле 'student_id' обязательно"
        }), 400
    
    full_name = data.get('full_name')
    class_number = data.get('class')
    group_id = data.get('group_id')
    tg_name = data.get('tg_name')
    
    # Проверяем, что хотя бы одно поле для обновления передано
    if all(field is None for field in [full_name, class_number, group_id, tg_name]):
        return jsonify({
            "status": False,
            "error": "Необходимо указать хотя бы одно поле для обновления"
        }), 400
    
    # Валидация класса, если передан
    if class_number is not None:
        try:
            class_number = int(class_number)
        except (ValueError, TypeError):
            return jsonify({
                "status": False,
                "error": "Поле 'class' должно быть числом"
            }), 400
    
    answer = edit_student(student_id, full_name, class_number, group_id, tg_name)
    http_code = 200 if answer.get('status') else 400
    return jsonify(answer), http_code


@app.route("/api/validate-student-by-tg", methods=['POST'])
def validate_student_by_tg_route():
    """
    Проверяет существование студента по Telegram никнейму
    
    Ожидаемые данные в JSON:
    {
        "tg_name": "@username"
    }
    
    Возвращает:
    {
        "status": true/false,
        "message": "...",
        "student_data": {
            "student_id": 123,
            "full_name": "Имя Фамилия",
            "class": 10,
            "group_id": 5,
            "tg_name": "@username"
        }
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            "status": False,
            "error": "Данные не предоставлены"
        }), 400
    
    tg_name = data.get('tg_name')
    
    if not tg_name:
        return jsonify({
            "status": False,
            "error": "Поле 'tg_name' обязательно"
        }), 400
    
    answer = validate_student_by_tg_name(tg_name)
    http_code = 200 if answer.get('status') else 404
    return jsonify(answer), http_code








#Platon part
#добавляет в изученные 
# пример 

# {
#     "student_id": 123,
#     "question_id": 456
# }

@app.route('/add-learned-question', methods=['POST'])
@require_self_or_role('student_id', 'admin', 'proctor')
def add_learned_question(current_user=None):
    connection = None
    cursor = None
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        question_id = data.get('question_id')
        
        if not student_id or not question_id:
            return jsonify({
                "success": False,
                "error": "Both student_id and question_id are required"
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Сначала получаем theme_id для данного вопроса
        get_theme_query = "SELECT theme_id FROM cards WHERE id = %s"
        cursor.execute(get_theme_query, (question_id,))
        question_data = cursor.fetchone()
        
        if not question_data:
            return jsonify({
                "success": False,
                "error": "Question not found",
                "question_id": question_id
            }), 404

        theme_id = question_data['theme_id']

        # 2. Проверяем, не существует ли уже такая запись
        check_query = """
        SELECT 1 FROM student_progress 
        WHERE student_id = %s AND question_id = %s
        """
        cursor.execute(check_query, (student_id, question_id))
        
        if cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Record already exists",
                "student_id": student_id,
                "question_id": question_id
            }), 409

        # 3. Добавляем новую запись с theme_id
        insert_query = """
        INSERT INTO student_progress 
        (student_id, question_id, theme_id) 
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_query, (student_id, question_id, theme_id))
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Record added successfully",
            "student_id": student_id,
            "question_id": question_id,
            "theme_id": theme_id
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

    finally:
        if connection:
            close_db_connection(connection)


#возвращает вообще все вопросы по теме и помечает те что уде изучены булиевой переменной - "is_learned": (true/false),
@app.route('/all-cards-by-theme/<int:student_id>/<int:theme_id>', methods=['GET'])
@require_self_or_role('student_id', 'admin', 'proctor')
def get_cards_by_theme_with_progress(student_id, theme_id, current_user=None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Получаем все карточки темы
        cards_query = "SELECT * FROM cards WHERE theme_id = %s"
        cursor.execute(cards_query, (theme_id,))
        all_cards = cursor.fetchall()

        # Получаем изученные карточки студента
        learned_query = """
        SELECT question_id 
        FROM student_progress 
        WHERE student_id = %s AND theme_id = %s
        """
        cursor.execute(learned_query, (student_id, theme_id))
        learned_card_ids = {row['question_id'] for row in cursor.fetchall()}

        # Добавляем флаг is_learned к каждой карточке
        for card in all_cards:
            card['is_learned'] = card['id'] in learned_card_ids

        return jsonify({
            "success": True,
            "student_id": student_id,
            "theme_id": theme_id,
            "cards": all_cards,
            "total_cards": len(all_cards),
            "learned_cards": len(learned_card_ids),
            "remaining_cards": len(all_cards) - len(learned_card_ids)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500
    finally:
        if connection:
            close_db_connection(connection)


#возвращает все карточки который пользователь еще не изучил
@app.route('/cadrs-by-theme/<int:student_id>/<int:theme_id>', methods=['GET'])
@require_self_or_role('student_id', 'admin', 'proctor')
def get_cards_to_learn(student_id, theme_id, current_user=None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Запрос для получения карточек, которые студент еще не изучил
        query = """
        SELECT c.* 
        FROM cards c
        WHERE c.theme_id = %s
        AND NOT EXISTS (
            SELECT 1 
            FROM student_progress sp
            WHERE sp.student_id = %s 
            AND sp.question_id = c.id
        )
        """
        cursor.execute(query, (theme_id, student_id))
        
        cards_to_learn = cursor.fetchall()

        return jsonify({
            "success": True,
            "student_id": student_id,
            "theme_id": theme_id,
            "cards_to_learn": cards_to_learn,
            "count": len(cards_to_learn)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500
    finally:
        if connection:
            close_db_connection(connection)
    

#можно добавлять неограниченное колличество карточек на тему, если темы не существует то создает эту тему и под новый id добавляет вопросы
#пример
# {
#     "name": "Название темы",
#     "questions": [
#         {
#             "question": "Текст вопроса 1",
#             "answer": "Ответ на вопрос 1"
#         },
#     ]
# }

@app.route('/create-theme-with-questions', methods=['POST'])
@require_role('admin')
def create_theme_with_questions(current_user=None):
    connection = None
    cursor = None
    try:
        data = request.get_json()
        
        # Получаем данные темы
        theme_name = data.get('name')
        questions = data.get('questions', [])  # Список вопросов
        
        if not theme_name:
            return jsonify({
                "success": False,
                "error": "Theme name is required"
            }), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # 1. Проверяем существование темы
        cursor.execute("SELECT id FROM card_themes WHERE name = %s", (theme_name,))
        existing_theme = cursor.fetchone()

        if existing_theme:
            theme_id = existing_theme['id']
            message = "Theme already exists"
        else:
            # 2. Создаем новую тему
            cursor.execute(
                "INSERT INTO card_themes (name) VALUES (%s)", 
                (theme_name,)
            )
            theme_id = cursor.lastrowid
            message = "Theme created successfully"
            connection.commit()

        # 3. Добавляем вопросы к теме
        added_questions = []
        for question_data in questions:
            question = question_data.get('question')
            answer = question_data.get('answer')
            
            if not question or not answer:
                continue  # Пропускаем неполные вопросы

            cursor.execute(
                """INSERT INTO cards 
                (question, answer, theme_id) 
                VALUES (%s, %s, %s)""",
                (question, answer, theme_id)
            )
            added_questions.append({
                "question": question,
                "answer": answer,
                "id": cursor.lastrowid
            })

        connection.commit()

        return jsonify({
            "success": True,
            "message": message,
            "theme_id": theme_id,
            "theme_name": theme_name,
            "added_questions": added_questions,
            "questions_count": len(added_questions)
        })

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

    finally:
        if connection:
            close_db_connection(connection)


#возвращает все темы
@app.route('/get-themes', methods=['GET'])
def get_all_themes():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM card_themes")
        themes = cursor.fetchall() 
        
        # Возвращаем результат в формате JSON
        return jsonify(themes)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    finally:
        if connection:
            close_db_connection(connection)
    

#возвращает выученные вопросы по конкретной теме
@app.route('/learned-questions/<int:student_id>/<int:theme_id>', methods=['GET'])
@require_self_or_role('student_id', 'admin', 'proctor')
def get_learned_questions(student_id, theme_id, current_user=None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        
        query = """
        SELECT c.* 
        FROM cards c
        JOIN student_progress sp ON c.id = sp.question_id
        WHERE sp.student_id = %s 
          AND c.theme_id = %s
        """
        cursor.execute(query, (student_id, theme_id))
        
        learned_questions = cursor.fetchall()

        return jsonify({
            "success": True,
            "student_id": student_id,
            "theme_id": theme_id,
            "learned_questions": learned_questions,
            "count": len(learned_questions)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500
    finally:
        if connection:
            close_db_connection(connection)


#убирает из изученных карточку
@app.route('/remove-learned-question/<int:student_id>/<int:question_id>', methods=['DELETE'])
@require_self_or_role('student_id', 'admin', 'proctor')
def remove_learned_question(student_id, question_id, current_user=None):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Проверяем существование записи перед удалением
        check_query = """
        SELECT 1 FROM student_progress 
        WHERE student_id = %s AND question_id = %s
        """
        cursor.execute(check_query, (student_id, question_id))
        
        if not cursor.fetchone():
            return jsonify({
                "success": False,
                "message": "Record not found",
                "student_id": student_id,
                "question_id": question_id
            }), 404

        # Удаляем запись
        delete_query = """
        DELETE FROM student_progress 
        WHERE student_id = %s AND question_id = %s
        """
        cursor.execute(delete_query, (student_id, question_id))
        connection.commit()
        
        affected_rows = cursor.rowcount

        return jsonify({
            "success": True,
            "message": "Record deleted successfully",
            "student_id": student_id,
            "question_id": question_id,
            "affected_rows": affected_rows
        })

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500
    finally:
        if connection:
            close_db_connection(connection)


# ============================================================================
# РОУТЫ ДЛЯ РАСПИСАНИЯ ЗАНЯТИЙ
# ============================================================================

@app.route("/api/schedule", methods=['GET'])
@require_role('admin', 'student')
def get_schedule(current_user=None):
    """
    Получить все занятия из расписания
    
    Возвращает:
    {
        "status": true/false,
        "message": "...",
        "schedule": [
            {
                "_id": "ObjectId",
                "day_of_week": "Понедельник",
                "start_time": "09:00",
                "end_time": "10:30",
                "lesson_name": "Математика",
                "teacher_name": "Иванов И.И.",
                "location": "Аудитория 101",
                "created_at": "datetime",
                "updated_at": "datetime"
            }
        ]
    }
    """
    try:
        # Используем реальный код для получения расписания из MongoDB
        schedule_manager = ScheduleManager()
        result = schedule_manager.get_all_schedule()
        schedule_manager.close_connection()
        
        http_code = 200 if result.get('status') else 500
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/schedule", methods=['POST'])
@require_role('admin')
def add_lesson(current_user=None):
    """
    Добавить новое занятие в расписание
    
    Ожидаемые данные в JSON:
    {
        "day_of_week": "Понедельник",  // Понедельник, Вторник, Среда, Четверг, Пятница, Суббота, Воскресенье
        "start_time": "09:00",         // формат HH:MM
        "end_time": "10:30",           // формат HH:MM
        "lesson_name": "Математика",
        "teacher_name": "Иванов И.И.",
        "location": "Аудитория 101"
    }
    
    Возвращает:
    {
        "status": true/false,
        "message": "...",
        "lesson_id": "ObjectId"  // только при успехе
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": False,
                "error": "Данные не предоставлены"
            }), 400
        
        # Используем реальный код для добавления занятия
        schedule_manager = ScheduleManager()
        result = schedule_manager.add_lesson(data)
        schedule_manager.close_connection()
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/schedule/<lesson_id>", methods=['PUT'])
@require_role('admin')
def edit_lesson(lesson_id, current_user=None):
    """
    Редактировать занятие в расписании
    
    URL параметр: lesson_id - ID занятия в MongoDB
    
    Ожидаемые данные в JSON:
    {
        "day_of_week": "Понедельник",
        "start_time": "09:00",
        "end_time": "10:30",
        "lesson_name": "Математика",
        "teacher_name": "Иванов И.И.",
        "location": "Аудитория 101"
    }
    
    Возвращает:
    {
        "status": true/false,
        "message": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": False,
                "error": "Данные не предоставлены"
            }), 400
        
        # Используем реальный код для редактирования занятия
        schedule_manager = ScheduleManager()
        result = schedule_manager.edit_lesson(lesson_id, data)
        schedule_manager.close_connection()
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/schedule/<lesson_id>", methods=['DELETE'])
@require_role('admin')
def delete_lesson(lesson_id, current_user=None):
    """
    Удалить занятие из расписания
    
    URL параметр: lesson_id - ID занятия в MongoDB
    
    Возвращает:
    {
        "status": true/false,
        "message": "..."
    }
    """
    try:
        # Используем реальный код для удаления занятия
        schedule_manager = ScheduleManager()
        result = schedule_manager.delete_lesson(lesson_id)
        schedule_manager.close_connection()
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


# ============================================================================
# РОУТЫ ДЛЯ ЗАПРОСОВ НА ОТГУЛ (ZAP)
# ============================================================================

@app.route("/api/create-zap", methods=['POST'])
@require_self_or_role('student_id', 'admin')
def create_zap_route(current_user=None):
    """
    Создать запрос на отгул от студента
    
    Ожидаемые данные в JSON:
    {
        "student_id": 123,
        "text": "Текст запроса",
        "images": ["base64_image1", "base64_image2", ...]  // необязательно
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": False,
                "error": "Данные не предоставлены"
            }), 400
        
        student_id = data.get('student_id')
        text = data.get('text')
        images_base64 = data.get('images', [])
        
        if not student_id or not text:
            return jsonify({
                "status": False,
                "error": "student_id и text обязательны"
            }), 400
        
        # Приводим student_id к int
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return jsonify({
                "status": False,
                "error": "student_id должен быть числом"
            }), 400
        
        # Преобразуем base64 файлы в blob и определяем тип
        images_data = []
        for img_base64 in images_base64:
            try:
                # Определяем тип файла из data URL
                file_type = 'image/jpeg'  # по умолчанию
                if ',' in img_base64:
                    mime_type = img_base64.split(',')[0].split(':')[1].split(';')[0]
                    file_type = mime_type
                    img_base64 = img_base64.split(',')[1]
                
                img_blob = base64.b64decode(img_base64)
                images_data.append({
                    "data": img_blob,
                    "type": file_type
                })
            except Exception as e:
                return jsonify({
                    "status": False,
                    "error": f"Ошибка обработки файла: {str(e)}"
                }), 400
        
        result = create_zap(student_id, text, images_data if images_data else None)
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/get-zaps-student", methods=['POST'])
@require_self_or_role('student_id', 'admin')
def get_zaps_student_route(current_user=None):
    """
    Получить запросы на отгул студента
    
    Ожидаемые данные в JSON:
    {
        "student_id": 123
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": False,
                "error": "Данные не предоставлены"
            }), 400
        
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({
                "status": False,
                "error": "student_id обязателен"
            }), 400
        
        # Приводим к int
        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return jsonify({
                "status": False,
                "error": "student_id должен быть числом"
            }), 400
        
        result = get_zaps_by_student(student_id)
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        print(f"Ошибка в get_zaps_student_route: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/get-all-zaps", methods=['GET'])
@require_role('admin')
def get_all_zaps_route(current_user=None):
    """
    Получить все запросы на отгул (для админов)
    
    Query параметры (необязательно):
    ?status=set  // фильтр по статусу ('set', 'apr', 'dec')
    """
    try:
        status = request.args.get('status', None)
        
        result = get_all_zaps(status)
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/get-zap/<zap_id>", methods=['GET'])
@require_role('admin')
def get_zap_route(zap_id, current_user=None):
    """
    Получить запрос на отгул по ID с изображениями
    
    URL параметр: zap_id - ID запроса
    """
    try:
        result = get_zap_by_id(zap_id)
        
        if result.get('status'):
            # Преобразуем blob файлы в base64 с правильным типом
            for img in result.get('images', []):
                if img.get('img'):
                    img_base64 = base64.b64encode(img['img']).decode('utf-8')
                    # Определяем правильный MIME тип
                    file_type = img.get('type', 'image/jpeg')
                    img['img_base64'] = f"data:{file_type};base64,{img_base64}"
                    img['file_type'] = file_type
                    # Удаляем blob из ответа (чтобы не передавать большие данные)
                    img['img'] = None
        
        http_code = 200 if result.get('status') else 404
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


@app.route("/api/process-zap", methods=['POST'])
@require_role('admin')
def process_zap_route(current_user=None):
    """
    Обработать запрос на отгул (одобрить/отклонить)
    При одобрении можно привязать к датам в посещаемости
    
    Ожидаемые данные в JSON:
    {
        "zap_id": 123,
        "status": "apr",  // 'apr' - одобрено, 'dec' - отклонено
        "answer": "Ваш ответ",
        "dates": ["2025-01-15", "2025-01-16"]  // необязательно, даты для привязки
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": False,
                "error": "Данные не предоставлены"
            }), 400
        
        zap_id = data.get('zap_id')
        status = data.get('status')
        answer = data.get('answer', '')
        dates = data.get('dates', [])
        
        if not zap_id or not status:
            return jsonify({
                "status": False,
                "error": "zap_id и status обязательны"
            }), 400
        
        if status not in ['apr', 'dec']:
            return jsonify({
                "status": False,
                "error": "status должен быть 'apr' или 'dec'"
            }), 400
        
        result = process_zap(zap_id, status, answer, dates if dates else None)
        
        http_code = 200 if result.get('status') else 400
        return jsonify(result), http_code
        
    except Exception as e:
        return jsonify({
            "status": False,
            "error": f"Внутренняя ошибка сервера: {str(e)}"
        }), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80,debug=False,threaded=True)



