import mysql.connector
from db import db
from get_groups import get_all_groups
from student_group_filter import get_student_ids_and_names_by_group
from get_proctor_bygroupid import get_proctor_by_group
def merge_groups_students_proctors():
    answer = []
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)
    groups = get_all_groups()['res']
    for item in groups:
        group_id = item['group_id']
        student_ids_and_names = get_student_ids_and_names_by_group(group_id)
        students_data = []
        for student in student_ids_and_names['res']:
            students_data.append(student)
        proctor = get_proctor_by_group(group_id)
        answer.append({'item':item,'students': students_data,'proctor': proctor})
        
    connection.close()
    return answer

