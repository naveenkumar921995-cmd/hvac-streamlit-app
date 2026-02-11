import bcrypt
from database import get_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def create_user(username, password, role="Admin"):
    conn = get_connection()
    c = conn.cursor()
    hashed = hash_password(password)
    c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
              (username, hashed, role))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    data = c.fetchone()
    conn.close()

    if data:
        return verify_password(password, data[0])
    return False
