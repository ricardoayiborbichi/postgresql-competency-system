import psycopg2
from config import TEST_DB_CONFIG

# Conectar a Ubuntu
conn = psycopg2.connect(**TEST_DB_CONFIG)
cur = conn.cursor()

# ID del usuario (cambia por el que tengas)
user_id = 1

# Establecer search_path
cur.execute(f"SET search_path TO user_{user_id}")
print(f"✅ search_path set to user_{user_id}")

# Verificar qué tablas hay en user_1
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'user_1'")
tables = cur.fetchall()
print(f"📋 Tablas en user_1: {tables}")

# Ejecutar el GRANT
try:
    cur.execute("GRANT SELECT ON employees TO CTF_READER_PRIV_1")
    conn.commit()
    print("✅ GRANT ejecutado correctamente")
except Exception as e:
    print(f"❌ Error: {e}")

cur.close()
conn.close()