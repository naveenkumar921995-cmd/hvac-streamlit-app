import bcrypt
from database import get_connection

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def create_admin():
    conn = get_connection()
    c = conn.cursor()

    hashed = hash_password("Admin@123")

    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ("admin", hashed, "Admin"))
        conn.commit()
    except:
        pass

    conn.close()
