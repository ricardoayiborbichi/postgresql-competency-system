import psycopg2

print("🔧 Подключение к базе данных...")

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="exam_system",
    user="app_user",
    password="app_password"
)

cur = conn.cursor()

print("✅ Подключено. Создание таблиц...")

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(50),
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Таблица users создана")

cur.execute("""
CREATE TABLE IF NOT EXISTS access_codes (
    id SERIAL PRIMARY KEY,
    access_code VARCHAR(20) NOT NULL UNIQUE,
    expires_at TIMESTAMP
)
""")
print("✓ Таблица access_codes создана")

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    variant INTEGER NOT NULL,
    task_number INTEGER NOT NULL,
    theme VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    flag_value VARCHAR(255) NOT NULL
)
""")
print("✓ Таблица tasks создана")

cur.execute("""
CREATE TABLE IF NOT EXISTS task_steps (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    instruction TEXT NOT NULL,
    check_query TEXT NOT NULL
)
""")
print("✓ Таблица task_steps создана")

# BUG FIX 1: variant era NOT NULL pero en login() se inserta sin variant.
# Ahora variant tiene DEFAULT NULL y se actualiza después en /exam/<variant>
cur.execute("""
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    variant INTEGER,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_score INTEGER DEFAULT 0
)
""")
print("✓ Таблица exams создана")

# BUG FIX 2: Faltaba UNIQUE(exam_id, task_id) para que funcione ON CONFLICT en submit_flag
cur.execute("""
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id),
    is_correct BOOLEAN DEFAULT FALSE,
    flag_entered VARCHAR(255),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, task_id)
)
""")
print("✓ Таблица results создана")

# BUG FIX 3: Faltaba UNIQUE(exam_id, step_id) para que funcione ON CONFLICT en checkers.py
cur.execute("""
CREATE TABLE IF NOT EXISTS step_results (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES task_steps(id),
    is_completed BOOLEAN DEFAULT FALSE,
    user_sql TEXT,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, step_id)
)
""")
print("✓ Таблица step_results создана")

cur.execute("""
CREATE TABLE IF NOT EXISTS flags (
    id SERIAL PRIMARY KEY,
    exam_id INTEGER REFERENCES exams(id) ON DELETE CASCADE,
    task_id INTEGER REFERENCES tasks(id),
    flag_value VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
print("✓ Таблица flags создана")

conn.commit()
cur.close()
conn.close()

print("\n✅ Все таблицы успешно созданы!")