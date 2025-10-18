from flask import Flask, jsonify, request
from flask_cors import CORS
from auth import auth
from aun import aun
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
from db_connect import get_db_connection
import mysql.connector
from edit_homework_session import edit_homework_session
from add_student import add_student
from edit_student import edit_student
from validate_student_by_tg import validate_student_by_tg_name
from schedule_manager import ScheduleManager

app = Flask(__name__)
CORS(app, resources={
    r"/*": {  # Обратите внимание на "/*" вместо "/api/*"
        "origins": ["https://cpm-lms.ru", "http://localhost:3000"],  # Только разрешенные домены
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

@app.route("/")
def hello_world():
    """
    Обработчик для маршрута '/'.
    Возвращает JSON с приветствием.
    """
    return jsonify({"answer": "hello world!"})

@app.route("/api/auth",methods = ['POST'])
def auth_route():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    body_login = data.get('login')  # Получаем значение ключа 'login'
    body_password = data.get('password')  # Получаем значение ключа 'password'
    answer = auth(body_login,body_password)
    return jsonify(answer)

@app.route("/api/aun",methods = ['POST'])
def aun_route():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    role = data.get('role')  # Получаем значение ключа 'login'
    id = data.get('id')  # Получаем значение ключа 'password'
    answer = aun(role,id)
    return jsonify(answer)

@app.route("/api/student-group-filter",methods = ['POST'])
def student_group_filter():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    id = data.get('id')  # Получаем значение ключа 'password'
    answer = get_student_ids_and_names_by_group(id)
    return jsonify(answer)

@app.route("/api/get-homeworks")
def gethomeworks():
    return jsonify(get_homeworks())

@app.route("/api/get-homework-sessions",methods = ['POST'])
def ghs():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    proctor_id = data.get('proctorId') 
    homework_id = data.get('homeworkId') 
    answer =get_proctor_homework_sessions(proctor_id,homework_id)
    return jsonify(answer)

@app.route("/api/pass_homework", methods=['POST'])
def pass_hw():
    """
    Получает дату из HTTP запроса в формате YYYY-MM-DD и возвращает данные.
    """
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
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


@app.route("/api/get-homeworks-student",methods = ['POST'])
def ghst():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id = data.get('studentId') 
    answer = get_student_homework_dashboard(student_id)
    return jsonify(answer)

@app.route("/api/edit-homework-session", methods=['POST'])
def edit_hw_session():
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

@app.route("/api/create-homework",methods = ['POST'])
def create_hw():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    name = data.get('homeworkName') 
    typee = data.get('homeworkType') 
    deadline_str = data.get('deadline') 
    answer = create_homework_and_sessions(name,typee,deadline_str)
    return jsonify(answer)
    
@app.route("/api/delete-homework",methods = ['POST'])
def delete_hw():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    homework_id = data.get('homeworkId')
    answer = delete_homework(homework_id) 
    return jsonify(answer)

@app.route("/api/get-groups-students",methods = ['GET'])
def get_groups_students():
    answer = merge_groups_students_proctors()
    return jsonify(answer)

@app.route("/api/get-unsigned-proctors-students",methods = ['GET'])
def get_unsigned_p_s():
    answer = get_unassigned_students_and_proctors()
    return jsonify(answer)


@app.route("/api/remove-groupd-id-student",methods = ['POST'])
def remove_g_s():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id= data.get('studentId')
    answer = reset_group_for_user('student',student_id)
    return jsonify(answer)


@app.route("/api/remove-groupd-id-proctor",methods = ['POST'])
def remove_g_p():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    proctor_id= data.get('proctorId')
    answer = reset_group_for_user('proctor',proctor_id)
    return jsonify(answer)


@app.route("/api/change-group-proctor",methods = ['POST'])
def change_p():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    proctor_id= data.get('proctorId')
    group_id = data.get('groupId')
    answer = assign_proctor_to_group(proctor_id,group_id)
    return jsonify(answer)


@app.route("/api/change-group-student",methods = ['POST'])
def change_s():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id= data.get('studentId')
    group_id = data.get('groupId')
    print(group_id)
    answer = assign_student_to_group(student_id,group_id)
    return jsonify(answer)


@app.route("/api/get-groups",methods = ['GET'])
def get_g():
    answer = get_all_groups()
    return jsonify(answer)


@app.route("/api/get-attendance-by-date",methods = ['POST'])
def get_attendance_by_d():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    date= data.get('date')
    answer = get_attendance_by_date(date)
    return jsonify(answer)


@app.route("/api/get-attendance-by-month",methods = ['POST'])
def get_attendance_by_m():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    month= data.get('month')
    year= data.get('year')
    answer = get_attendance_diary(year,month)
    return jsonify(answer)


@app.route("/api/add-attendance",methods = ['POST'])
def add_attendance_f():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id= data.get('studentId')
    date= data.get('date')
    answer = add_attendance(student_id,date)
    return jsonify(answer)


@app.route("/api/get-users-by-role",methods = ['POST'])
def get_users_br():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    role= data.get('role')
    answer = get_users_by_role(role)
    return jsonify(answer)


@app.route("/api/delete-user",methods = ['POST'])
def del_us():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    role= data.get('role')
    user_id= data.get('userId')
    answer = delete_user(role,user_id)
    return jsonify(answer)


@app.route("/api/get-students")
def get_us():
    answer = get_all_students()
    return jsonify(answer)


@app.route("/api/add-student", methods=['POST'])
def add_student_route():
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
def edit_student_route():
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
def add_learned_question():
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

    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": str(e),
            "student_id": student_id,
            "question_id": question_id
        }), 500

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


#возвращает вообще все вопросы по теме и помечает те что уде изучены булиевой переменной - "is_learned": (true/false),
@app.route('/all-cards-by-theme/<int:student_id>/<int:theme_id>', methods=['GET'])
def get_cards_by_theme_with_progress(student_id, theme_id):
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

        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "student_id": student_id,
            "theme_id": theme_id,
            "cards": all_cards,
            "total_cards": len(all_cards),
            "learned_cards": len(learned_card_ids),
            "remaining_cards": len(all_cards) - len(learned_card_ids)
        })

    except mysql.connector.Error as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "student_id": student_id,
            "theme_id": theme_id
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500


#возвращает все карточки который пользователь еще не изучил
@app.route('/cadrs-by-theme/<int:student_id>/<int:theme_id>', methods=['GET'])
def get_cards_to_learn(student_id, theme_id):
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
        
        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "student_id": student_id,
            "theme_id": theme_id,
            "cards_to_learn": cards_to_learn,
            "count": len(cards_to_learn)
        })

    except mysql.connector.Error as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "student_id": student_id,
            "theme_id": theme_id
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500
    

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
def create_theme_with_questions():
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

    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


#возвращает все темы
@app.route('/get-themes', methods=['GET'])
def get_all_themes():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT * FROM card_themes")
        themes = cursor.fetchall() 
        cursor.close()
        connection.close()
        
        # Возвращаем результат в формате JSON
        return jsonify(themes)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    

#возвращает выученные вопросы по конкретной теме
@app.route('/learned-questions/<int:student_id>/<int:theme_id>', methods=['GET'])
def get_learned_questions(student_id, theme_id):
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
        
        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "student_id": student_id,
            "theme_id": theme_id,
            "learned_questions": learned_questions,
            "count": len(learned_questions)
        })

    except mysql.connector.Error as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "student_id": student_id,
            "theme_id": theme_id
        }), 500


#убирает из изученных карточку
@app.route('/remove-learned-question/<int:student_id>/<int:question_id>', methods=['DELETE'])
def remove_learned_question(student_id, question_id):
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
            cursor.close()
            connection.close()
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
        
        cursor.close()
        connection.close()

        return jsonify({
            "success": True,
            "message": "Record deleted successfully",
            "student_id": student_id,
            "question_id": question_id,
            "affected_rows": affected_rows
        })

    except mysql.connector.Error as e:
        connection.rollback()
        return jsonify({
            "success": False,
            "error": str(e),
            "student_id": student_id,
            "question_id": question_id
        }), 500

    except Exception as e:
        connection.rollback()
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "details": str(e)
        }), 500


# ============================================================================
# РОУТЫ ДЛЯ РАСПИСАНИЯ ЗАНЯТИЙ
# ============================================================================

@app.route("/api/schedule", methods=['GET'])
def get_schedule():
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
def add_lesson():
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
def edit_lesson(lesson_id):
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
def delete_lesson(lesson_id):
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


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=80,debug=True)



