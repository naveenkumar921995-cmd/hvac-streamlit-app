import sqlite3

DB_NAME = "site.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def create_tables():
    conn = get_connection()
    c = conn.cursor()

    # Users
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # Assets
    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        department TEXT,
        location TEXT,
        health INTEGER,
        amc_end TEXT,
        compliance_end TEXT
    )
    """)

    # Energy
    c.execute("""
    CREATE TABLE IF NOT EXISTS energy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        asset_name TEXT,
        kwh REAL,
        cost_per_kwh REAL
    )
    """)

    # Attendance
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        login_time TEXT,
        logout_time TEXT
    )
    """)

    conn.commit()
    conn.close()
