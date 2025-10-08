import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('email_assistant.db')
cursor = conn.cursor()

# 모든 사용자 조회
cursor.execute('SELECT id, email FROM users')
users = cursor.fetchall()
print("등록된 사용자:", users)

conn.close()