import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="exam_system",
    user="app_user",
    password="app_password"
)
cur = conn.cursor()

print("🔧 Corrigiendo check_queries (mayúsculas → minúsculas)...")

# Obtener todos los pasos
cur.execute("SELECT id, check_query FROM task_steps ORDER BY id")
steps = cur.fetchall()

fixes = {
    # Variante 1 - Roles
    "rolname='CTF_ROLE_1'":    "rolname='ctf_role_1'",
    "rolname='CTF_STUDENT_1'": "rolname='ctf_student_1'",
    "'CTF_ROLE_1'":            "'ctf_role_1'",
    "'CTF_STUDENT_1'":         "'ctf_student_1'",
    "grantee = 'CTF_STUDENT_1'": "grantee = 'ctf_student_1'",
    "'CTF_STUDENT_1', 'ctf_admin": "'ctf_student_1', 'ctf_admin",

    # Variante 1 - Auth
    "rolname='CTF_USER_AUTH_1'":    "rolname='ctf_user_auth_1'",
    "rolname='CTF_READER_AUTH_1'":  "rolname='ctf_reader_auth_1'",
    "'CTF_USER_AUTH_1'":            "'ctf_user_auth_1'",
    "'CTF_READER_AUTH_1'":          "'ctf_reader_auth_1'",

    # Variante 1 - Priv
    "rolname='CTF_READER_PRIV_1'":  "rolname='ctf_reader_priv_1'",
    "rolname='CTF_AUDITOR_1'":      "rolname='ctf_auditor_1'",
    "'CTF_READER_PRIV_1'":          "'ctf_reader_priv_1'",
    "'CTF_AUDITOR_1'":              "'ctf_auditor_1'",

    # Variante 2 - Roles
    "rolname='CTF_ROLE_2'":    "rolname='ctf_role_2'",
    "rolname='CTF_STUDENT_2'": "rolname='ctf_student_2'",
    "'CTF_ROLE_2'":            "'ctf_role_2'",
    "'CTF_STUDENT_2'":         "'ctf_student_2'",

    # Variante 2 - Auth
    "rolname='CTF_USER_AUTH_2'":   "rolname='ctf_user_auth_2'",
    "rolname='CTF_READER_AUTH_2'": "rolname='ctf_reader_auth_2'",
    "'CTF_USER_AUTH_2'":           "'ctf_user_auth_2'",
    "'CTF_READER_AUTH_2'":         "'ctf_reader_auth_2'",

    # Variante 2 - Priv
    "rolname='CTF_EDITOR_PRIV_2'": "rolname='ctf_editor_priv_2'",
    "rolname='CTF_OPERATOR_2'":    "rolname='ctf_operator_2'",
    "'CTF_EDITOR_PRIV_2'":         "'ctf_editor_priv_2'",
    "'CTF_OPERATOR_2'":            "'ctf_operator_2'",

    # Variante 3 - Roles
    "rolname='CTF_ROLE_3'":    "rolname='ctf_role_3'",
    "rolname='CTF_STUDENT_3'": "rolname='ctf_student_3'",
    "'CTF_ROLE_3'":            "'ctf_role_3'",
    "'CTF_STUDENT_3'":         "'ctf_student_3'",

    # Variante 3 - Auth
    "rolname='CTF_USER_AUTH_3'":   "rolname='ctf_user_auth_3'",
    "rolname='CTF_READER_AUTH_3'": "rolname='ctf_reader_auth_3'",
    "'CTF_USER_AUTH_3'":           "'ctf_user_auth_3'",
    "'CTF_READER_AUTH_3'":         "'ctf_reader_auth_3'",

    # Variante 3 - Priv
    "rolname='CTF_AUDITOR_PRIV_3'": "rolname='ctf_auditor_priv_3'",
    "rolname='CTF_AUDITOR_3'":      "rolname='ctf_auditor_3'",
    "'CTF_AUDITOR_PRIV_3'":         "'ctf_auditor_priv_3'",
    "'CTF_AUDITOR_3'":              "'ctf_auditor_3'",

    # has_table_privilege — usuario en minúsculas
    "has_table_privilege('CTF_STUDENT_1'": "has_table_privilege('ctf_student_1'",
    "has_table_privilege('CTF_STUDENT_2'": "has_table_privilege('ctf_student_2'",
    "has_table_privilege('CTF_STUDENT_3'": "has_table_privilege('ctf_student_3'",
    "has_table_privilege('CTF_READER_AUTH_1'": "has_table_privilege('ctf_reader_auth_1'",
    "has_table_privilege('CTF_READER_AUTH_2'": "has_table_privilege('ctf_reader_auth_2'",
    "has_table_privilege('CTF_READER_AUTH_3'": "has_table_privilege('ctf_reader_auth_3'",
    "has_table_privilege('CTF_READER_PRIV_1'": "has_table_privilege('ctf_reader_priv_1'",
    "has_table_privilege('CTF_EDITOR_PRIV_2'": "has_table_privilege('ctf_editor_priv_2'",
    "has_table_privilege('CTF_AUDITOR_PRIV_3'": "has_table_privilege('ctf_auditor_priv_3'",
    "has_table_privilege('CTF_AUDITOR_1'": "has_table_privilege('ctf_auditor_1'",
    "has_table_privilege('CTF_AUDITOR_3'": "has_table_privilege('ctf_auditor_3'",
}

for step_id, check_query in steps:
    new_query = check_query
    for old, new in fixes.items():
        new_query = new_query.replace(old, new)

    if new_query != check_query:
        cur.execute("UPDATE task_steps SET check_query = %s WHERE id = %s", (new_query, step_id))
        print(f"  ✓ Paso id={step_id} corregido")
    else:
        print(f"  · Paso id={step_id} sin cambios")

conn.commit()

# Verificar resultado
print("\n📋 Check queries actualizadas:")
cur.execute("SELECT id, step_number, check_query FROM task_steps ORDER BY id")
for row in cur.fetchall():
    print(f"  Paso id={row[0]}, step={row[1]}: {row[2][:80]}...")

cur.close()
conn.close()
print("\n✅ ¡Corrección completada!")