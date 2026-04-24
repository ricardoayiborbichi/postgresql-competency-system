import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="exam_system",
    user="app_user",
    password="app_password"
)
cur = conn.cursor()

# Primero ver qué tareas existen
print("📋 Tareas encontradas en la BD:")
cur.execute("SELECT id, variant, task_number, theme FROM tasks ORDER BY variant, task_number")
all_tasks = cur.fetchall()
for t in all_tasks:
    print(f"  id={t[0]} | Variante {t[1]} | Tarea {t[2]} | {t[3]}")

print()

flag_steps = [
    (1, 1, 'ctf_admin.CTF_FLAG_1'),
    (1, 2, 'ctf_admin.CTF_FLAG_AUTH_1'),
    (1, 3, 'ctf_admin.CTF_FLAG_PRIV_1'),
    (2, 1, 'ctf_admin.CTF_FLAG_2'),
    (2, 2, 'ctf_admin.CTF_FLAG_AUTH_2'),
    (2, 3, 'ctf_admin.CTF_FLAG_PRIV_2'),
    (3, 1, 'ctf_admin.CTF_FLAG_3'),
    (3, 2, 'ctf_admin.CTF_FLAG_AUTH_3'),
    (3, 3, 'ctf_admin.CTF_FLAG_PRIV_3'),
]

print("➕ Añadiendo paso 'Получите флаг'...")
for variant, task_number, flag_table in flag_steps:
    # Buscar tarea
    cur.execute("SELECT id FROM tasks WHERE variant = %s AND task_number = %s", (variant, task_number))
    row = cur.fetchone()
    if not row:
        print(f"  ⚠ No encontrada: Variante {variant} Tarea {task_number} — saltando")
        continue
    task_id = row[0]

    # Ver si ya existe el paso de flag
    cur.execute("""
        SELECT id FROM task_steps 
        WHERE task_id = %s AND instruction LIKE '%%Получите флаг%%'
    """, (task_id,))
    if cur.fetchone():
        print(f"  · Variante {variant} Tarea {task_number}: ya tiene paso de флаг")
        continue

    # Obtener número del último paso
    cur.execute("SELECT COALESCE(MAX(step_number), 0) FROM task_steps WHERE task_id = %s", (task_id,))
    max_step = cur.fetchone()[0]
    next_step = max_step + 1

    instruction = (
        f'Получите флаг. Выполните SELECT-запрос к таблице {flag_table}.\n'
        f'Команда: SELECT flag_value FROM {flag_table};\n'
        f'Скопируйте полученное значение флага в поле ниже.'
    )
    check_query = f'SELECT flag_value FROM {flag_table}'

    cur.execute("""
        INSERT INTO task_steps (task_id, step_number, instruction, check_query)
        VALUES (%s, %s, %s, %s)
    """, (task_id, next_step, instruction, check_query))

    print(f"  ✓ Variante {variant} Tarea {task_number}: Шаг {next_step} añadido")

conn.commit()
cur.close()
conn.close()
print("\n✅ ¡Listo!")