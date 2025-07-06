import mysql.connector
from db import db

def get_all_exams():
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        password=db.password,
        database=db.db
    )
    
    cursor = connection.cursor(dictionary=True)
    
    try:
        # Получаем все экзамены
        cursor.execute("SELECT id, name, date FROM exams")
        exams = cursor.fetchall()
        
        result = []
        
        for exam in exams:
            # Получаем вопросы для этого экзамена
            cursor.execute("""
                SELECT id, question, answer 
                FROM questions 
                WHERE exam_id = %s
            """, (exam['id'],))
            questions = cursor.fetchall()
            
            # Получаем сессии для этого экзамена
            cursor.execute("""
                SELECT es.id, es.result as session_result, 
                       s.id as student_id, s.full_name as student_name
                FROM exams_sessions es
                JOIN students s ON es.student_id = s.id
                WHERE es.exam_id = %s
            """, (exam['id'],))
            sessions = cursor.fetchall()
            
            exam_data = {
                'exam_id': exam['id'],
                'exam_name': exam['name'],
                'exam_date': exam['date'],
                'questions': [],
                'sessions': []
            }
            
            # Добавляем вопросы
            for question in questions:
                exam_data['questions'].append({
                    'question_id': question['id'],
                    'question_text': question['question'],
                    'correct_answer': question['answer']
                })
            
            # Добавляем сессии с ответами студентов
            for session in sessions:
                cursor.execute("""
                    SELECT ea.question_id, ea.result as answer_result,
                           q.question, q.answer as correct_answer
                    FROM exams_answers ea
                    JOIN questions q ON ea.question_id = q.id
                    WHERE ea.exam_session_id = %s
                """, (session['id'],))
                answers = cursor.fetchall()
                
                session_data = {
                    'session_id': session['id'],
                    'student_id': session['student_id'],
                    'student_name': session['student_name'],
                    'session_result': session['session_result'],
                    'answers': []
                }
                
                for answer in answers:
                    session_data['answers'].append({
                        'question_id': answer['question_id'],
                        'question_text': answer['question'],
                        'correct_answer': answer['correct_answer'],
                        'student_answer_result': answer['answer_result']
                    })
                
                exam_data['sessions'].append(session_data)
            
            result.append(exam_data)
        
        return result
        
    finally:
        cursor.close()
        connection.close()

print(get_all_exams())