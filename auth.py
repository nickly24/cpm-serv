import mysql.connector
from db import db



def auth(username,password):
    # Connect to server
    cnx = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password)

    # Get a cursor
    cur = cnx.cursor()

    # Execute a query
    cur.execute("SELECT * FROM auth_users WHERE username = %s and password = %s", (username,password))
    # Fetch one result
    row = cur.fetchall()
    if len(row) == 0:
        cnx.close()
        return {'status': False}
    else:
      
        if row[0][4] == 'student':
            cur.execute("SELECT  * FROM students WHERE id = %s", (row[0][2],))
            data = cur.fetchone()
            cnx.close()
            answer = {
                'sratus': True, 
                'res': {
                    'role': 'student',
                    'id': data[0],
                    'full_name': data[1],
                    'group_id': data[2]
                }
            }
            return answer
        
        if row[0][4] == 'proctor':
            cur.execute("SELECT  * FROM proctors WHERE id = %s", (row[0][2],))
            data = cur.fetchone()
            cnx.close()
            answer = {
                'sratus': True, 
                'res': {
                    'role': 'proctor',
                    'id': data[0],
                    'full_name': data[1],
                    'group_id': data[2]
                }
            }
            return answer
        
        if row[0][4] == 'examinator':
            cur.execute("SELECT  * FROM examinators WHERE id = %s", (row[0][2],))
            data = cur.fetchone()
            cnx.close()
            answer = {
                'sratus': True, 
                'res': {
                    'role': 'examinator',
                    'id': data[0],
                    'full_name': data[1],
                }
            }
            return answer
        
        if row[0][4] == 'admin':
            cur.execute("SELECT  * FROM admins WHERE id = %s", (row[0][2],))
            data = cur.fetchone()
            cnx.close()
            answer = {
                'sratus': True, 
                'res': {
                    'role': 'admin',
                    'id': data[0],
                    'full_name': data[1],
                    
                }
            }
            return answer
        
        if row[0][4] == 'supervisor':
            cur.execute("SELECT  * FROM supervisors WHERE id = %s", (row[0][2],))
            data = cur.fetchone()
            cnx.close()
            answer = {
                'sratus': True, 
                'res': {
                    'role': 'supervisor',
                    'id': data[0],
                    'full_name': data[1],
                }
            }
            return answer
        