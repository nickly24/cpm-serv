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
app = Flask(__name__)
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
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


    answer = pass_homework(session_id, date_object)
    return jsonify(answer)


@app.route("/api/get-homeworks-student",methods = ['POST'])
def ghst():
    data = request.get_json()  # Получаем данные из тела запроса в формате JSON
    student_id = data.get('studentId') 
    answer = get_student_homework_dashboard(student_id)
    return jsonify(answer)

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


@app.route("/api/get-exams")
def get_exams():
    answer = get_all_exams()
    return jsonify(answer)


if __name__ == "__main__":
    app.run(host='127.0.0.1',debug=True)



