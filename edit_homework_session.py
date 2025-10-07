import mysql.connector
from db import db
from datetime import datetime, date


def edit_homework_session(session_id, result=None, date_pass=None, status=None):
    connection = mysql.connector.connect(
        host=db.host,
        port=db.port,
        user=db.user,
        db=db.db,
        password=db.password
    )
    cursor = connection.cursor(dictionary=True)

    try:
        # Проверяем, что сессия существует
        cursor.execute("SELECT * FROM homework_sessions WHERE id = %s", (session_id,))
        session = cursor.fetchone()
        if not session:
            return {"status": False, "error": "session_not_found"}

        # Готовим набор обновляемых полей
        set_clauses = []
        values = []

        if result is not None:
            try:
                result_val = int(result)
                if result_val < 0:
                    result_val = 0
                if result_val > 100:
                    result_val = 100
                set_clauses.append("result = %s")
                values.append(result_val)
            except (TypeError, ValueError):
                return {"status": False, "error": "invalid_result"}

        if date_pass is not None:
            # Поддержка str в ISO формате или datetime/date
            if isinstance(date_pass, str):
                try:
                    date_val = date.fromisoformat(date_pass)
                except ValueError:
                    try:
                        date_val = datetime.strptime(date_pass, "%Y-%m-%d").date()
                    except ValueError:
                        return {"status": False, "error": "invalid_date_pass"}
            elif isinstance(date_pass, datetime):
                date_val = date_pass.date()
            elif isinstance(date_pass, date):
                date_val = date_pass
            else:
                return {"status": False, "error": "invalid_date_pass_type"}

            set_clauses.append("date_pass = %s")
            values.append(date_val)

        if status is not None:
            try:
                status_val = int(status)
                if status_val not in (0, 1):
                    return {"status": False, "error": "invalid_status"}
                set_clauses.append("status = %s")
                values.append(status_val)
            except (TypeError, ValueError):
                return {"status": False, "error": "invalid_status"}

        if not set_clauses:
            return {"status": False, "error": "nothing_to_update"}

        update_sql = f"UPDATE homework_sessions SET {', '.join(set_clauses)} WHERE id = %s"
        values.append(session_id)
        cursor.execute(update_sql, tuple(values))
        connection.commit()

        return {"status": True}

    except mysql.connector.Error as err:
        connection.rollback()
        return {"status": False, "error": str(err)}
    finally:
        connection.close()


