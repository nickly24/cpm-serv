from db_pool import get_db_connection, close_db_connection

def aun(role, user_id):
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        user_tables = {
            'student': {
                'table': 'students',
                'fields': ['id', 'full_name', 'group_id']
            },
            'proctor': {
                'table': 'proctors',
                'fields': ['id', 'full_name', 'group_id']
            },
            'admin': {
                'table': 'admins',
                'fields': ['id', 'full_name']
            },
            'examinator': {
                'table': 'examinators',
                'fields': ['id', 'full_name']
            },
            'supervisor': {
                'table': 'supervisors',
                'fields': ['id', 'full_name']
            }
        }

        if role not in user_tables:
            return {"status": False}

        table_info = user_tables[role]
        table_name = table_info['table']
        fields = table_info['fields']
        columns = ", ".join(fields)

        query = f"SELECT {columns} FROM {table_name} WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()

        if not result:
            return {"status": False}

        response = {
            "status": True,
            "role": role,
            "entity_id": result['id'],
            "full_name": result['full_name'],
            "group_id": result.get('group_id', None)
        }

        return response
    except Exception as e:
        print(f"Ошибка в aun: {str(e)}")
        return {"status": False}
    finally:
        # Возвращаем подключение в пул
        if connection:
            close_db_connection(connection)

# === ПРИМЕР ВЫЗОВА ===
