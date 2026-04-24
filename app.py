# app.py
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from config import SECRET_KEY
from utils.db import get_app_db_connection, cleanup_test_db, cleanup_session_data
from utils.checkers import check_step, get_flag

app = Flask(__name__)
app.secret_key = SECRET_KEY


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('name')
        access_code = request.form.get('access_code')

        conn = get_app_db_connection()
        if not conn:
            return render_template('login.html', error='Ошибка подключения к БД')

        cur = conn.cursor()

        # Проверка кода доступа
        cur.execute("""
            SELECT id, access_code FROM access_codes 
            WHERE access_code = %s 
            AND (expires_at IS NULL OR expires_at > NOW())
        """, (access_code,))

        code = cur.fetchone()

        if code:
            # Создать пользователя
            cur.execute("""
                INSERT INTO users (name) VALUES (%s) RETURNING id
            """, (name,))
            user_id = cur.fetchone()[0]

            # Создать сессию тестирования
            cur.execute("""
                INSERT INTO exams (user_id) VALUES (%s) RETURNING id
            """, (user_id,))
            exam_id = cur.fetchone()[0]

            conn.commit()

            # ========== СОЗДАТЬ СХЕМУ В UBUNTU ==========
            try:
                conn_test = get_test_db_connection()
                cur_test = conn_test.cursor()
                # Проверить, существует ли уже схема
                cur_test.execute("SELECT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'user_' || %s)", (user_id,))
                exists = cur_test.fetchone()[0]

                if not exists:
                    cur_test.callproc('create_user_schema', (user_id,))
                    conn_test.commit()
                    print(f"✅ Схема user_{user_id} создана в Ubuntu")
                else:
                    print(f"ℹ️ Схема user_{user_id} уже существует")
                cur_test.close()
                conn_test.close()
            except Exception as e:
                print(f"⚠️ Ошибка при создании схемы: {e}")
            # =============================================

            session['user_id'] = user_id
            session['user_name'] = name
            session['exam_id'] = exam_id

            cur.close()
            conn.close()
            return redirect(url_for('select_variant'))
        else:
            cur.close()
            conn.close()
            return render_template('login.html', error='Неверный код доступа')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user_name=session.get('user_name'))


@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')
    user_name = session.get('user_name')

    conn = get_app_db_connection()
    cur = conn.cursor()

    # Solo exámenes completados (con end_time)
    cur.execute("""
        SELECT e.id, e.variant, e.total_score, e.start_time
        FROM exams e
        WHERE e.user_id = %s 
          AND e.end_time IS NOT NULL
          AND e.variant IS NOT NULL
        ORDER BY e.start_time DESC
    """, (user_id,))
    raw_exams = cur.fetchall()

    exams = []
    for ex in raw_exams:
        exam_id = ex[0]
        variant = ex[1]
        score = ex[2] or 0
        date = ex[3].strftime('%d.%m.%Y %H:%M') if ex[3] else '—'

        cur.execute("SELECT COUNT(*) FROM tasks WHERE variant = %s", (variant,))
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM results WHERE exam_id = %s AND is_correct = TRUE", (exam_id,))
        correct = cur.fetchone()[0]

        cur.execute("""
            SELECT t.task_number, t.theme, r.is_correct
            FROM tasks t
            LEFT JOIN results r ON r.task_id = t.id AND r.exam_id = %s
            WHERE t.variant = %s
            ORDER BY t.task_number
        """, (exam_id, variant))
        tasks = [{'number': r[0], 'theme': r[1], 'is_correct': r[2]} for r in cur.fetchall()]

        exams.append({
            'variant': variant, 'score': score,
            'correct': correct, 'total': total,
            'date': date, 'tasks': tasks
        })

    cur.close()
    conn.close()

    return render_template('history.html', user_name=user_name, exams=exams)


@app.route('/select_variant')
def select_variant():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('variant.html')


@app.route('/exam/<int:variant>')
def exam(variant):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    exam_id = session.get('exam_id')
    print(f"🔍 exam: user_id={session.get('user_id')}, exam_id={exam_id}")  # DEBUG

    conn = get_app_db_connection()
    cur = conn.cursor()

    session['variant'] = variant
    cur.execute("UPDATE exams SET variant = %s WHERE id = %s", (variant, exam_id))
    conn.commit()

    cur.execute("""
        SELECT id, task_number, theme, description 
        FROM tasks WHERE variant = %s ORDER BY task_number
    """, (variant,))
    tasks = cur.fetchall()

    tasks_with_steps = []
    for task in tasks:
        cur.execute("""
            SELECT id, step_number, instruction, check_query
            FROM task_steps WHERE task_id = %s ORDER BY step_number
        """, (task[0],))
        steps = [{
            'id': s[0],
            'number': s[1],
            'instruction': s[2],
            'is_flag': s[3].strip().lower().startswith('select flag_value')
        } for s in cur.fetchall()]

        tasks_with_steps.append({
            'id': task[0], 'number': task[1],
            'theme': task[2], 'description': task[3],
            'steps': steps
        })

    # Загрузить прогресс выполнения шагов
    cur.execute("""
        SELECT step_id, is_completed, user_sql FROM step_results 
        WHERE exam_id = %s
    """, (exam_id,))
    completed_steps = {}
    saved_sql = {}
    for row in cur.fetchall():
        completed_steps[row[0]] = row[1]
        if row[2]:
            saved_sql[row[0]] = row[2]

    # Загрузить выполненные задания
    cur.execute("""
        SELECT task_id FROM results 
        WHERE exam_id = %s AND is_correct = TRUE
    """, (exam_id,))
    completed_tasks = {row[0] for row in cur.fetchall()}

    cur.close()
    conn.close()

    return render_template('exam.html',
                           variant=variant,
                           tasks=tasks_with_steps,
                           completed_steps=completed_steps,
                           completed_tasks=completed_tasks,
                           saved_sql=saved_sql)


@app.route('/check_step', methods=['POST'])
def check_step_route():
    data = request.get_json()
    user_id = session.get('user_id')
    exam_id = session.get('exam_id')
    print(f"🔍 check_step_route: user_id={user_id}, exam_id={exam_id}")  # DEBUG
    print(f"🔍 SQL recibido: {data.get('user_sql', '')[:100]}")  # DEBUG
    result = check_step(data['step_id'], data['user_sql'], user_id, exam_id)
    print(f"🔍 Resultado: {result}")  # DEBUG
    return jsonify(result)


@app.route('/get_flag', methods=['POST'])
def get_flag_route():
    data = request.get_json()
    result = get_flag(data['task_id'], session.get('user_id'), session.get('exam_id'))
    return jsonify(result)


@app.route('/submit_flag', methods=['POST'])
def submit_flag():
    data = request.get_json()
    task_id = data['task_id']
    flag = data['flag']
    exam_id = session.get('exam_id')

    conn = get_app_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT flag_value FROM tasks WHERE id = %s", (task_id,))
    expected_flag = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM task_steps 
        WHERE task_id = %s AND check_query NOT ILIKE 'SELECT flag_value%%'
    """, (task_id,))
    total_normal = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*) FROM step_results sr
        JOIN task_steps ts ON ts.id = sr.step_id
        WHERE sr.exam_id = %s AND ts.task_id = %s 
          AND ts.check_query NOT ILIKE 'SELECT flag_value%%'
          AND sr.is_completed = TRUE
    """, (exam_id, task_id))
    completed_normal = cur.fetchone()[0]

    if completed_normal < total_normal:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': '⛔ Сначала выполните все шаги задания!'})

    if flag == expected_flag:
        cur.execute("""
            INSERT INTO results (exam_id, task_id, is_correct, flag_entered)
            VALUES (%s, %s, TRUE, %s)
            ON CONFLICT (exam_id, task_id) DO UPDATE SET
                is_correct = TRUE, flag_entered = EXCLUDED.flag_entered, completed_at = NOW()
        """, (exam_id, task_id, flag))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Задание выполнено!'})
    else:
        cur.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Неверный флаг. Попробуйте ещё раз.'})


@app.route('/finish')
def finish():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    exam_id = session.get('exam_id')
    user_name = session.get('user_name')
    variant = session.get('variant', 1)

    conn = get_app_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM tasks WHERE variant = %s", (variant,))
    total_tasks = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM results WHERE exam_id = %s AND is_correct = TRUE", (exam_id,))
    correct_count = cur.fetchone()[0]

    cur.execute("""
        SELECT t.task_number, t.theme, r.is_correct
        FROM tasks t
        LEFT JOIN results r ON r.task_id = t.id AND r.exam_id = %s
        WHERE t.variant = %s ORDER BY t.task_number
    """, (exam_id, variant))
    task_details = cur.fetchall()

    score = (correct_count / total_tasks * 100) if total_tasks > 0 else 0
    cur.execute("UPDATE exams SET total_score = %s, end_time = NOW() WHERE id = %s", (score, exam_id))
    conn.commit()
    cur.close()
    conn.close()

    cleanup_test_db()
    cleanup_session_data(exam_id)
    session.clear()

    return render_template('result.html',
                           name=user_name,
                           score=score,
                           correct=correct_count,
                           total=total_tasks,
                           task_details=task_details)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)