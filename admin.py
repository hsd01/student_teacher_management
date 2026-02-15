from werkzeug.security import generate_password_hash
from db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute(
    "INSERT INTO users (username, password, role) VALUES (%s,%s,'admin')",
    ("admin", generate_password_hash("admin123"))
)

conn.commit()
cursor.close()
conn.close()

print("Admin created: admin / admin123")
