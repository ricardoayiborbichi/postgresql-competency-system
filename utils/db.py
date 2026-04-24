# utils/db.py
import psycopg2
from config import APP_DB_CONFIG, TEST_DB_CONFIG

# Orden: primero usuarios/miembros, luego roles base
CTF_MEMBERS = [
    'ctf_student_1', 'ctf_student_2', 'ctf_student_3',
    'ctf_user_auth_1', 'ctf_user_auth_2', 'ctf_user_auth_3',
    'ctf_auditor_1', 'ctf_auditor_3',
    'ctf_operator_2',
]
CTF_ROLES = [
    'ctf_role_1', 'ctf_role_2', 'ctf_role_3',
    'ctf_reader_auth_1', 'ctf_reader_auth_2', 'ctf_reader_auth_3',
    'ctf_reader_priv_1',
    'ctf_editor_priv_2',
    'ctf_auditor_priv_3',
]
ALL_CTF = CTF_MEMBERS + CTF_ROLES


def get_app_db_connection():
    try:
        return psycopg2.connect(**APP_DB_CONFIG)
    except Exception as e:
        print(f"Ошибка подключения к app_db: {e}")
        return None


def get_test_db_connection(user_id=None):
    """
    Подключение к тестовой среде (Ubuntu).
    search_path = public, ctf_admin:
      - public    -> employees, salaries, orders, products
      - ctf_admin -> CTF_FLAG_1, CTF_FLAG_2... (таблицы с флагами)
    """
    print(f"🔍 get_test_db_connection: user_id={user_id}")
    try:
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SET search_path TO public, ctf_admin")
        print("🔍 search_path set to public, ctf_admin")
        cur.close()
        return conn
    except Exception as e:
        print(f"Ошибка подключения к test_db: {e}")
        return None


def cleanup_test_db():
    """
    Limpia todos los roles CTF de la BD de prueba.
    DROP OWNED BY elimina todos los privilegios antes de borrar el rol.
    Después recrea las tablas auxiliares por si fueron borradas accidentalmente.
    """
    try:
        conn = psycopg2.connect(**TEST_DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()

        # Paso 1: Borrar roles CTF
        for role in ALL_CTF:
            try:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,))
                if cur.fetchone():
                    cur.execute(f"DROP OWNED BY {role} CASCADE")
                    cur.execute(f"DROP ROLE IF EXISTS {role}")
            except Exception:
                pass

        # Paso 2: Recrear tablas auxiliares si fueron borradas por DROP OWNED BY
        for table in ['employees', 'salaries', 'orders', 'products']:
            try:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table} (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        value TEXT
                    )
                """)
            except Exception:
                pass

        # Cerrar después de todo
        cur.close()
        conn.close()
        print("✅ Test DB limpiada")
        return True
    except Exception as e:
        print(f"⚠ Error limpiando test DB: {e}")
        return False


def cleanup_session_data(exam_id):
    """
    Limpia los datos temporales de la sesión:
    - step_results: pasos completados (solo útiles durante el examen)
    NO borra: exams ni results (son el historial permanente del usuario)
    """
    try:
        conn = get_app_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM step_results WHERE exam_id = %s", (exam_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠ Error limpiando datos de sesión: {e}")