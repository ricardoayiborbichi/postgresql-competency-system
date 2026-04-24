# utils/checkers.py
import psycopg2
from utils.db import get_test_db_connection, get_app_db_connection


def check_step(step_id, user_sql, user_id, exam_id):
    """
    Verifica el SQL del usuario en la BD de prueba.
    """
    print(f"🔍 check_step: user_id={user_id}, step_id={step_id}")
    print(f"🔍 SQL: {user_sql[:100]}")

    conn_app = get_app_db_connection()
    if not conn_app:
        return {'success': False, 'message': 'Ошибка подключения к БД приложения'}

    cur_app = conn_app.cursor()
    cur_app.execute("SELECT check_query FROM task_steps WHERE id = %s", (step_id,))
    row = cur_app.fetchone()
    cur_app.close()
    conn_app.close()

    if not row:
        return {'success': False, 'message': 'Шаг не найден'}

    check_query = row[0].strip()

    # Блокировать intento de obtener flag desde paso normal
    if check_query.lower().startswith('select flag_value'):
        return {'success': False, 'message': 'Используйте кнопку «ПОЛУЧИТЬ ФЛАГ».'}

    conn_test = get_test_db_connection(user_id)
    if not conn_test:
        return {'success': False, 'message': 'Ошибка подключения к тестовой БД'}

    cur_test = conn_test.cursor()
    sql_error_msg = None

    # ========== DEBUG: Verificar search_path y tablas ==========
    try:
        cur_test.execute("SHOW search_path")
        search_path = cur_test.fetchone()
        print(f"🔍 search_path actual: {search_path}")

        cur_test.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'employees')")
        table_exists = cur_test.fetchone()
        print(f"🔍 employees existe en search_path? {table_exists}")

        cur_test.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'user_1' AND table_name = 'employees')")
        table_in_user1 = cur_test.fetchone()
        print(f"🔍 employees existe en user_1? {table_in_user1}")
    except Exception as e:
        print(f"⚠️ Error en debug: {e}")
    # ============================================================

    try:
        # Ejecutar SQL del usuario
        cur_test.execute(user_sql)
        conn_test.commit()
    except psycopg2.Error as e:
        conn_test.rollback()
        sql_error_msg = str(e).split('\n')[0]
    except Exception as e:
        conn_test.rollback()
        cur_test.close()
        conn_test.close()
        return {'success': False, 'message': f'Ошибка: {str(e)}'}

    try:
        # Verificar resultado con check_query
        cur_test.execute(check_query)
        check_result = cur_test.fetchone()

        if check_result and check_result[0]:
            # Guardar que el paso fue completado Y guardar el SQL
            _mark_step_completed(exam_id, step_id, user_sql)
            return {'success': True, 'message': 'Шаг выполнен правильно!'}
        else:
            if sql_error_msg:
                return {'success': False, 'message': f'Ошибка SQL: {sql_error_msg}'}
            else:
                return {'success': False, 'message': 'Команда выполнена, но результат неверный. Проверьте параметры.'}

    except psycopg2.Error as e:
        conn_test.rollback()
        return {'success': False, 'message': f'Ошибка проверки: {str(e).split(chr(10))[0]}'}
    finally:
        cur_test.close()
        conn_test.close()


def get_flag(task_id, user_id, exam_id):
    """
    Obtiene el flag SOLO si todos los pasos normales están completados.
    """
    conn_app = get_app_db_connection()
    if not conn_app:
        return {'success': False, 'message': 'Ошибка подключения к БД приложения'}

    cur_app = conn_app.cursor()
    cur_app.execute("""
        SELECT id, step_number, check_query 
        FROM task_steps 
        WHERE task_id = %s 
        ORDER BY step_number
    """, (task_id,))
    all_steps = cur_app.fetchall()

    normal_steps = [(s[0], s[1]) for s in all_steps
                    if not s[2].strip().lower().startswith('select flag_value')]
    flag_step = next((s for s in all_steps
                      if s[2].strip().lower().startswith('select flag_value')), None)

    if not flag_step:
        cur_app.close()
        conn_app.close()
        return {'success': False, 'message': 'Флаг для этого задания не найден.'}

    # Verificar que todos los pasos normales están completados
    if normal_steps:
        normal_ids = [s[0] for s in normal_steps]
        cur_app.execute("""
            SELECT step_id FROM step_results
            WHERE exam_id = %s AND step_id = ANY(%s) AND is_completed = TRUE
        """, (exam_id, normal_ids))
        completed_ids = {r[0] for r in cur_app.fetchall()}
        incomplete = [s for s in normal_steps if s[0] not in completed_ids]

        if incomplete:
            nums = ', '.join(str(s[1]) for s in incomplete)
            cur_app.close()
            conn_app.close()
            return {
                'success': False,
                'message': f'⛔ Сначала выполните шаги: {nums}. Флаг доступен только после выполнения всех шагов!'
            }

    cur_app.close()
    conn_app.close()

    # Todos los pasos OK → obtener flag de la BD de prueba
    conn_test = get_test_db_connection(user_id)
    if not conn_test:
        return {'success': False, 'message': 'Ошибка подключения к тестовой БД'}

    cur_test = conn_test.cursor()
    try:
        cur_test.execute(flag_step[2].strip())
        result = cur_test.fetchone()

        if result and result[0]:
            # Marcar paso de flag como completado
            _mark_step_completed(exam_id, flag_step[0], None)
            return {
                'success': True,
                'message': 'Флаг получен!',
                'flag_value': result[0]
            }
        else:
            return {'success': False,
                    'message': 'Не удалось получить флаг. Убедитесь, что все шаги выполнены корректно.'}

    except psycopg2.Error as e:
        return {'success': False, 'message': f'Ошибка: {str(e).split(chr(10))[0]}'}
    finally:
        cur_test.close()
        conn_test.close()


def _mark_step_completed(exam_id, step_id, user_sql=None):
    """
    Marca el paso como completado.
    Guarda el SQL si se proporciona.
    """
    try:
        conn_app = get_app_db_connection()
        cur_app = conn_app.cursor()

        if user_sql:
            cur_app.execute("""
                INSERT INTO step_results (exam_id, step_id, is_completed, user_sql)
                VALUES (%s, %s, TRUE, %s)
                ON CONFLICT (exam_id, step_id) DO UPDATE SET
                    is_completed = TRUE, user_sql = EXCLUDED.user_sql, completed_at = NOW()
            """, (exam_id, step_id, user_sql))
        else:
            cur_app.execute("""
                INSERT INTO step_results (exam_id, step_id, is_completed)
                VALUES (%s, %s, TRUE)
                ON CONFLICT (exam_id, step_id) DO UPDATE SET
                    is_completed = TRUE, completed_at = NOW()
            """, (exam_id, step_id))

        conn_app.commit()
        cur_app.close()
        conn_app.close()
        print(f"✅ Paso {step_id} marcado como completado")
    except Exception as e:
        print(f"Error marcando paso: {e}")