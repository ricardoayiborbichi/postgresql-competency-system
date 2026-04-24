import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="exam_system",
    user="app_user",
    password="app_password"
)
cur = conn.cursor()

print("🧹 Limpiando datos anteriores...")
cur.execute("DELETE FROM step_results")
cur.execute("DELETE FROM results")
cur.execute("DELETE FROM task_steps")
cur.execute("DELETE FROM tasks")
conn.commit()

# ==============================================================
# ESTRUCTURA:
# Variante 1 → Tarea 1 (Roles), Tarea 2 (Auth), Tarea 3 (Priv)
# Variante 2 → Tarea 1 (Roles), Tarea 2 (Auth), Tarea 3 (Priv)
# Variante 3 → Tarea 1 (Roles), Tarea 2 (Auth), Tarea 3 (Priv)
# ==============================================================

tasks = [
    # ── VARIANTE 1 ────────────────────────────────────────────
    {
        'variant': 1, 'task_number': 1,
        'theme': 'Пользователи и роли',
        'flag_value': 'FLAG{role_1_a1b2c3d4}',
        'description': (
            'Контекст: Вы работаете в качестве администратора базы данных в компании «ТехноСервис». '
            'Иванов Иван — новый сотрудник отдела аналитики. '
            'Шаг 1. Создайте роль CTF_ROLE_1 с возможностью входа. Пароль CTF_PASS_1. '
            'Запретите создание БД и других ролей. Лимит подключений: 5. Срок действия: до 31.12.2025. '
            'Шаг 2. Создайте пользователя CTF_STUDENT_1 с паролем ctf_student_1. Назначьте ему роль CTF_ROLE_1. '
            'Шаг 3. Предоставьте пользователю CTF_STUDENT_1 право на чтение таблицы ctf_admin.CTF_FLAG_1. '
            'Шаг 4. Получите флаг.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': 'Создайте роль CTF_ROLE_1 с возможностью входа в систему. Установите пароль CTF_PASS_1. Запретите этой роли создавать базы данных и другие роли. Установите лимит подключений не более 5 одновременных сессий. Срок действия пароля установите до 31 декабря 2025 года.',
                'check_query': "SELECT rolcanlogin AND NOT rolcreatedb AND NOT rolcreaterole AND rolconnlimit = 5 AND rolvaliduntil::date = '2025-12-31' FROM pg_roles WHERE rolname='CTF_ROLE_1'"
            },
            {
                'step_number': 2,
                'instruction': 'Создайте пользователя CTF_STUDENT_1 с паролем ctf_student_1. Назначьте ему роль CTF_ROLE_1.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_STUDENT_1' AND rolcanlogin=true) AND EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_ROLE_1') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_STUDENT_1'))"
            },
            {
                'step_number': 3,
                'instruction': 'Предоставьте пользователю CTF_STUDENT_1 право на чтение данных из таблицы ctf_admin.CTF_FLAG_1.',
                'check_query': "SELECT has_table_privilege('CTF_STUDENT_1', 'ctf_admin.CTF_FLAG_1', 'SELECT')"
            },
        ]
    },
    {
        'variant': 1, 'task_number': 2,
        'theme': 'Политики паролей',
        'flag_value': 'FLAG{auth_1_m3n4o5p6}',
        'description': (
            'Контекст: Вы — администратор безопасности БД в компании «КиберЗащита». '
            'Необходимо настроить политику аутентификации с использованием SCRAM-SHA-256. '
            'Шаг 1. Измените метод шифрования паролей на SCRAM-SHA-256. '
            'Шаг 2. Создайте пользователя CTF_USER_AUTH_1. Срок действия пароля до 31.03.2026. '
            'Шаг 3. Создайте роль CTF_READER_AUTH_1 и предоставьте ей SELECT на ctf_admin.CTF_FLAG_AUTH_1. '
            'Шаг 4. Назначьте роль CTF_READER_AUTH_1 пользователю CTF_USER_AUTH_1.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': "Измените метод шифрования паролей на SCRAM-SHA-256 (если он ещё не установлен).\nКоманда: ALTER SYSTEM SET password_encryption = 'scram-sha-256'; SELECT pg_reload_conf();",
                'check_query': "SELECT COUNT(*) > 0 FROM pg_settings WHERE name='password_encryption' AND setting='scram-sha-256'"
            },
            {
                'step_number': 2,
                'instruction': "Создайте пользователя CTF_USER_AUTH_1 с паролем CTF_PASS_AUTH_1. Установите срок действия пароля до 31 марта 2026 года.",
                'check_query': "SELECT rolvaliduntil >= '2026-03-31' FROM pg_roles WHERE rolname='CTF_USER_AUTH_1'"
            },
            {
                'step_number': 3,
                'instruction': 'Создайте роль CTF_READER_AUTH_1. Предоставьте этой роли право на чтение таблицы ctf_admin.CTF_FLAG_AUTH_1.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_READER_AUTH_1' AND rolcanlogin=false) AND has_table_privilege('CTF_READER_AUTH_1', 'ctf_admin.CTF_FLAG_AUTH_1', 'SELECT')"
            },
            {
                'step_number': 4,
                'instruction': 'Назначьте пользователю CTF_USER_AUTH_1 роль CTF_READER_AUTH_1.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_READER_AUTH_1') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_USER_AUTH_1'))"
            },
        ]
    },
    {
        'variant': 1, 'task_number': 3,
        'theme': 'Привилегии (GRANT/REVOKE)',
        'flag_value': 'FLAG{priv_1_y5z6a7b8}',
        'description': (
            'Контекст: Вы — администратор БД в компании «ТоргСервис». Внешнему аудитору необходим доступ '
            'только для чтения определённых таблиц. '
            'Шаг 1. Создайте роль CTF_READER_PRIV_1 без права входа. '
            'Шаг 2. Предоставьте роли CTF_READER_PRIV_1 право SELECT на таблицу employees. '
            'Шаг 3. Создайте пользователя CTF_AUDITOR_1 с паролем ctf_auditor_1. '
            'Шаг 4. Назначьте пользователю CTF_AUDITOR_1 роль CTF_READER_PRIV_1. '
            'Шаг 5. Убедитесь, что CTF_AUDITOR_1 не имеет доступа к таблице salaries.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': 'Создайте роль CTF_READER_PRIV_1 без возможности входа в систему.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_READER_PRIV_1' AND rolcanlogin=false)"
            },
            {
                'step_number': 2,
                'instruction': 'Предоставьте роли CTF_READER_PRIV_1 право только на чтение данных из таблицы employees.',
                'check_query': "SELECT has_table_privilege('CTF_READER_PRIV_1', 'employees', 'SELECT')"
            },
            {
                'step_number': 3,
                'instruction': "Создайте пользователя CTF_AUDITOR_1 con contraseña ctf_auditor_1.",
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_AUDITOR_1' AND rolcanlogin=true)"
            },
            {
                'step_number': 4,
                'instruction': 'Назначьте пользователю CTF_AUDITOR_1 роль CTF_READER_PRIV_1.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_READER_PRIV_1') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_AUDITOR_1'))"
            },
            {
                'step_number': 5,
                'instruction': 'Убедитесь, что пользователь CTF_AUDITOR_1 не имеет доступа к таблице salaries. (Это проверяется автоматически — никаких дополнительных команд не требуется, если вы правильно выполнили предыдущие шаги.)',
                'check_query': "SELECT NOT has_table_privilege('CTF_AUDITOR_1', 'salaries', 'SELECT')"
            },
        ]
    },

    # ── VARIANTE 2 ────────────────────────────────────────────
    {
        'variant': 2, 'task_number': 1,
        'theme': 'Пользователи и роли',
        'flag_value': 'FLAG{role_2_e5f6g7h8}',
        'description': (
            'Контекст: Вы — администратор БД в компании «ФинансГрупп». Петров Петр — новый сотрудник отдела разработки. '
            'Ему необходимы права для создания тестовых баз данных. '
            'Шаг 1. Создайте роль CTF_ROLE_2 с правом входа, CREATEDB, без CREATEROLE, лимит 10. '
            'Шаг 2. Создайте пользователя CTF_STUDENT_2 и назначьте ему CTF_ROLE_2. '
            'Шаг 3. Предоставьте CTF_STUDENT_2 право SELECT на ctf_admin.CTF_FLAG_2.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': 'Создайте роль CTF_ROLE_2 с возможностью входа в систему. Установите пароль CTF_PASS_2. Разрешите этой роли создавать базы данных, но запретите создавать другие роли. Установите лимит подключений не более 10 одновременных сессий.',
                'check_query': "SELECT rolcanlogin AND rolcreatedb AND NOT rolcreaterole AND rolconnlimit = 10 FROM pg_roles WHERE rolname='CTF_ROLE_2'"
            },
            {
                'step_number': 2,
                'instruction': 'Создайте пользователя CTF_STUDENT_2 с паролем ctf_student_2. Назначьте ему роль CTF_ROLE_2.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_STUDENT_2' AND rolcanlogin=true) AND EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_ROLE_2') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_STUDENT_2'))"
            },
            {
                'step_number': 3,
                'instruction': 'Предоставьте пользователю CTF_STUDENT_2 право на чтение данных из таблицы ctf_admin.CTF_FLAG_2.',
                'check_query': "SELECT has_table_privilege('CTF_STUDENT_2', 'ctf_admin.CTF_FLAG_2', 'SELECT')"
            },
        ]
    },
    {
        'variant': 2, 'task_number': 2,
        'theme': 'Политики паролей',
        'flag_value': 'FLAG{auth_2_q7r8s9t0}',
        'description': (
            'Контекст: Вы — администратор БД в компании «МедТех». Необходимо настроить политику паролей '
            'с ограниченным сроком действия (90 дней). '
            'Шаг 1. Создайте пользователя CTF_USER_AUTH_2, срок действия пароля 90 дней. '
            'Шаг 2. Создайте роль CTF_READER_AUTH_2, предоставьте SELECT на ctf_admin.CTF_FLAG_AUTH_2. '
            'Шаг 3. Назначьте роль CTF_READER_AUTH_2 пользователю CTF_USER_AUTH_2.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': "Создайте пользователя CTF_USER_AUTH_2 с паролем CTF_PASS_AUTH_2. Установите срок действия пароля 90 дней от текущей даты.\nКоманда: CREATE USER CTF_USER_AUTH_2 WITH PASSWORD 'CTF_PASS_AUTH_2' VALID UNTIL CURRENT_DATE + INTERVAL '90 days';",
                'check_query': "SELECT rolvaliduntil >= CURRENT_DATE + INTERVAL '89 days' FROM pg_roles WHERE rolname='CTF_USER_AUTH_2'"
            },
            {
                'step_number': 2,
                'instruction': 'Создайте роль CTF_READER_AUTH_2. Предоставьте этой роли право на чтение таблицы ctf_admin.CTF_FLAG_AUTH_2.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_READER_AUTH_2' AND rolcanlogin=false) AND has_table_privilege('CTF_READER_AUTH_2', 'ctf_admin.CTF_FLAG_AUTH_2', 'SELECT')"
            },
            {
                'step_number': 3,
                'instruction': 'Назначьте пользователю CTF_USER_AUTH_2 роль CTF_READER_AUTH_2.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_READER_AUTH_2') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_USER_AUTH_2'))"
            },
        ]
    },
    {
        'variant': 2, 'task_number': 3,
        'theme': 'Привилегии (GRANT/REVOKE)',
        'flag_value': 'FLAG{priv_2_c9d0e1f2}',
        'description': (
            'Контекст: Вы — администратор БД в компании «ЛогистикПро». Новый сотрудник отдела заказов '
            'должен иметь права SELECT и UPDATE на таблицу orders, но без DELETE. '
            'Шаг 1. Создайте роль CTF_EDITOR_PRIV_2 без права входа. '
            'Шаг 2. Предоставьте роли SELECT и UPDATE на таблицу orders. '
            'Шаг 3. Создайте пользователя CTF_OPERATOR_2. '
            'Шаг 4. Назначьте роль CTF_EDITOR_PRIV_2 пользователю CTF_OPERATOR_2.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': 'Создайте роль CTF_EDITOR_PRIV_2 без возможности входа в систему.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_EDITOR_PRIV_2' AND rolcanlogin=false)"
            },
            {
                'step_number': 2,
                'instruction': 'Предоставьте роли CTF_EDITOR_PRIV_2 право на чтение и изменение данных в таблице orders. Удаление запрещено.',
                'check_query': "SELECT has_table_privilege('CTF_EDITOR_PRIV_2', 'orders', 'SELECT') AND has_table_privilege('CTF_EDITOR_PRIV_2', 'orders', 'UPDATE') AND NOT has_table_privilege('CTF_EDITOR_PRIV_2', 'orders', 'DELETE')"
            },
            {
                'step_number': 3,
                'instruction': "Создайте пользователя CTF_OPERATOR_2 с паролем ctf_operator_2.",
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_OPERATOR_2' AND rolcanlogin=true)"
            },
            {
                'step_number': 4,
                'instruction': 'Назначьте пользователю CTF_OPERATOR_2 роль CTF_EDITOR_PRIV_2.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_EDITOR_PRIV_2') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_OPERATOR_2'))"
            },
        ]
    },

    # ── VARIANTE 3 ────────────────────────────────────────────
    {
        'variant': 3, 'task_number': 1,
        'theme': 'Пользователи и роли',
        'flag_value': 'FLAG{role_3_i9j0k1l2}',
        'description': (
            'Контекст: Вы — администратор БД в компании «АудитПро». Светлана Сидорова — сотрудник '
            'отдела внутреннего аудита. Ей нужны права для управления ролями других сотрудников. '
            'Шаг 1. Создайте роль CTF_ROLE_3 с правом входа, CREATEROLE, без CREATEDB, лимит 3. '
            'Шаг 2. Создайте пользователя CTF_STUDENT_3 и назначьте CTF_ROLE_3. '
            'Шаг 3. Предоставьте CTF_STUDENT_3 право SELECT на ctf_admin.CTF_FLAG_3.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': 'Создайте роль CTF_ROLE_3 с возможностью входа в систему. Установите пароль CTF_PASS_3. Запретите этой роли создавать базы данных, но разрешите создавать другие роли. Установите лимит подключений не более 3 одновременных сессий.',
                'check_query': "SELECT rolcanlogin AND NOT rolcreatedb AND rolcreaterole AND rolconnlimit = 3 FROM pg_roles WHERE rolname='CTF_ROLE_3'"
            },
            {
                'step_number': 2,
                'instruction': 'Создайте пользователя CTF_STUDENT_3 с паролем ctf_student_3. Назначьте ему роль CTF_ROLE_3.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_STUDENT_3' AND rolcanlogin=true) AND EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_ROLE_3') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_STUDENT_3'))"
            },
            {
                'step_number': 3,
                'instruction': 'Предоставьте пользователю CTF_STUDENT_3 право на чтение данных из таблицы ctf_admin.CTF_FLAG_3.',
                'check_query': "SELECT has_table_privilege('CTF_STUDENT_3', 'ctf_admin.CTF_FLAG_3', 'SELECT')"
            },
        ]
    },
    {
        'variant': 3, 'task_number': 2,
        'theme': 'Политики паролей',
        'flag_value': 'FLAG{auth_3_u1v2w3x4}',
        'description': (
            'Контекст: Вы — администратор БД в компании «АйтиСервис». Внедряется новая политика безопасности '
            'с SCRAM-SHA-256 и сроком действия паролей 180 дней. '
            'Шаг 1. Измените метод шифрования на SCRAM-SHA-256. '
            'Шаг 2. Создайте пользователя CTF_USER_AUTH_3, срок действия 180 дней. '
            'Шаг 3. Создайте роль CTF_READER_AUTH_3 и предоставьте SELECT на ctf_admin.CTF_FLAG_AUTH_3. '
            'Шаг 4. Назначьте роль CTF_READER_AUTH_3 пользователю CTF_USER_AUTH_3.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': "Измените метод шифрования паролей на SCRAM-SHA-256.\nКоманда: ALTER SYSTEM SET password_encryption = 'scram-sha-256'; SELECT pg_reload_conf();",
                'check_query': "SELECT COUNT(*) > 0 FROM pg_settings WHERE name='password_encryption' AND setting='scram-sha-256'"
            },
            {
                'step_number': 2,
                'instruction': "Создайте пользователя CTF_USER_AUTH_3 с паролем CTF_PASS_AUTH_3. Установите срок действия пароля 180 дней от текущей даты.",
                'check_query': "SELECT rolvaliduntil >= CURRENT_DATE + INTERVAL '179 days' FROM pg_roles WHERE rolname='CTF_USER_AUTH_3'"
            },
            {
                'step_number': 3,
                'instruction': 'Создайте роль CTF_READER_AUTH_3. Предоставьте этой роли право на чтение таблицы ctf_admin.CTF_FLAG_AUTH_3.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_READER_AUTH_3' AND rolcanlogin=false) AND has_table_privilege('CTF_READER_AUTH_3', 'ctf_admin.CTF_FLAG_AUTH_3', 'SELECT')"
            },
            {
                'step_number': 4,
                'instruction': 'Назначьте пользователю CTF_USER_AUTH_3 роль CTF_READER_AUTH_3.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_READER_AUTH_3') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_USER_AUTH_3'))"
            },
        ]
    },
    {
        'variant': 3, 'task_number': 3,
        'theme': 'Привилегии (GRANT/REVOKE)',
        'flag_value': 'FLAG{priv_3_g3h4i5j6}',
        'description': (
            'Контекст: Вы — администратор БД в компании «Мультисервис». Аудитору необходим доступ '
            'только для чтения из таблиц employees и products. '
            'Шаг 1. Создайте роль CTF_AUDITOR_PRIV_3 без права входа. '
            'Шаг 2. Предоставьте SELECT на таблицы employees и products. '
            'Шаг 3. Создайте пользователя CTF_AUDITOR_3. '
            'Шаг 4. Назначьте роль CTF_AUDITOR_PRIV_3 пользователю CTF_AUDITOR_3.'
        ),
        'steps': [
            {
                'step_number': 1,
                'instruction': 'Создайте роль CTF_AUDITOR_PRIV_3 без возможности входа в систему.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_AUDITOR_PRIV_3' AND rolcanlogin=false)"
            },
            {
                'step_number': 2,
                'instruction': 'Предоставьте роли CTF_AUDITOR_PRIV_3 право только на чтение данных из таблиц employees и products.',
                'check_query': "SELECT has_table_privilege('CTF_AUDITOR_PRIV_3', 'employees', 'SELECT') AND has_table_privilege('CTF_AUDITOR_PRIV_3', 'products', 'SELECT')"
            },
            {
                'step_number': 3,
                'instruction': "Создайте пользователя CTF_AUDITOR_3 с паролем ctf_auditor_3.",
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='CTF_AUDITOR_3' AND rolcanlogin=true)"
            },
            {
                'step_number': 4,
                'instruction': 'Назначьте пользователю CTF_AUDITOR_3 роль CTF_AUDITOR_PRIV_3.',
                'check_query': "SELECT EXISTS (SELECT 1 FROM pg_auth_members WHERE roleid=(SELECT oid FROM pg_roles WHERE rolname='CTF_AUDITOR_PRIV_3') AND member=(SELECT oid FROM pg_roles WHERE rolname='CTF_AUDITOR_3'))"
            },
        ]
    },
]

# ── INSERT ────────────────────────────────────────────────────
print("📥 Insertando tareas y pasos...")
for task in tasks:
    cur.execute("""
        INSERT INTO tasks (variant, task_number, theme, description, flag_value)
        VALUES (%s, %s, %s, %s, %s) RETURNING id
    """, (task['variant'], task['task_number'], task['theme'], task['description'], task['flag_value']))
    task_id = cur.fetchone()[0]
    print(f"  ✓ Tarea insertada: Variante {task['variant']} - Tarea {task['task_number']} (id={task_id})")

    for step in task['steps']:
        cur.execute("""
            INSERT INTO task_steps (task_id, step_number, instruction, check_query)
            VALUES (%s, %s, %s, %s)
        """, (task_id, step['step_number'], step['instruction'], step['check_query']))
        print(f"      → Paso {step['step_number']} insertado")

conn.commit()

# ── INSERT CÓDIGOS DE ACCESO ──────────────────────────────────
print("\n🔑 Insertando códigos de acceso de prueba...")
access_codes = ['ADMIN2024', 'TEST1234', 'DEMO5678', 'EXAM9999', 'CTF00001']
for code in access_codes:
    cur.execute("""
        INSERT INTO access_codes (access_code, expires_at)
        VALUES (%s, NULL)
        ON CONFLICT (access_code) DO NOTHING
    """, (code,))
print(f"  ✓ Códigos insertados: {', '.join(access_codes)}")

conn.commit()
cur.close()
conn.close()

print("\n✅ ¡Base de datos poblada correctamente!")
print("\n📋 Resumen de flags por variante:")
print("  Variante 1: FLAG{role_1_a1b2c3d4} | FLAG{auth_1_m3n4o5p6} | FLAG{priv_1_y5z6a7b8}")
print("  Variante 2: FLAG{role_2_e5f6g7h8} | FLAG{auth_2_q7r8s9t0} | FLAG{priv_2_c9d0e1f2}")
print("  Variante 3: FLAG{role_3_i9j0k1l2} | FLAG{auth_3_u1v2w3x4} | FLAG{priv_3_g3h4i5j6}")
print("\n🔑 Códigos de acceso: ADMIN2024 | TEST1234 | DEMO5678 | EXAM9999 | CTF00001")