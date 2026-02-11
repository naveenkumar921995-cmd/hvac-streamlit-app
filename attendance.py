from database import get_connection
import datetime

def mark_login(name):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO attendance (name, date, login_time) VALUES (?, ?, ?)",
              (name, str(datetime.date.today()), str(datetime.datetime.now().time())))
    conn.commit()
    conn.close()
