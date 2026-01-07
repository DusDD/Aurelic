from data.db_get_connection import get_connection
from data.db_call import init_auth_schema
from auth.register import register_user

conn = get_connection()
init_auth_schema(conn)
conn.close()

user_id = register_user("alice", "MeinSicheresPasswort123!")
print("User registered with ID:", user_id)