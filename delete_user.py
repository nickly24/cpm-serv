import mysql.connector

def delete_user(role, user_id):
    connection = mysql.connector.connect(
        host="147.45.138.77",
        port=3306,
        user="minishep",
        password="qwerty!1",
        db="minishep"
    )
    cursor = connection.cursor()

    user_tables = {
        'student': 'students',
        'proctor': 'proctors',
        'admin': 'admins',
        'examinator': 'examinators',
        'supervisor': 'supervisors'
    }

    if role not in user_tables:
        connection.close()
        print("Ошибка: Неверная роль.")
        return

    try:
        # Удаляем из сущности
        table_name = user_tables[role]
        delete_entity_query = f"DELETE FROM {table_name} WHERE id = %s"
        cursor.execute(delete_entity_query, (user_id,))
        connection.commit()

        # Удаляем из auth_users
        delete_auth_query = "DELETE FROM auth_users WHERE role = %s AND ref_id = %s"
        cursor.execute(delete_auth_query, (role, user_id))
        connection.commit()

        print(f"Пользователь с ролью '{role}' и id '{user_id}' успешно удалён.")

    except mysql.connector.Error as err:
        print(f"Ошибка базы данных: {err}")
        connection.rollback()

    finally:
        connection.close()
