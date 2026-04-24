from utils.db import get_test_db_connection

conn = get_test_db_connection(user_id=1)
cur = conn.cursor()

check_query = "SELECT rolcanlogin AND NOT rolcreatedb AND NOT rolcreaterole AND rolconnlimit = 5 AND rolvaliduntil::date = '2025-12-31' FROM pg_roles WHERE rolname='ctf_role_1'"
cur.execute(check_query)
result = cur.fetchone()
print(f"Resultado: {result}")

cur.close()
conn.close()