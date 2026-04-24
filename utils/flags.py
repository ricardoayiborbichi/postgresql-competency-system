# utils/flags.py
import hashlib
import time

def generate_flag(task_name, user_id, task_id):
    """Генерация уникального флага"""
    unique_str = f"{task_name}_{user_id}_{task_id}_{time.time()}"
    hash_part = hashlib.md5(unique_str.encode()).hexdigest()[:12]
    return f"FLAG{{{task_name}_{hash_part}}}"