import sqlite3

DB_NAME = "data/controlroom.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # ASSETS
    c.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        department TEXT,
        location TEXT,
        health INTEGER DEFAULT 100
    )
    """)

    # ENERGY
    c.execute("""
    CREATE TABLE IF NOT EXISTS energy (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER,
        date TEXT,
        kwh REAL,
        btu REAL,
        cost REAL
    )
    """)

    # AMC
    c.execute("""
    CREATE TABLE IF NOT EXISTS amc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER,
        vendor TEXT,
        expiry_date TEXT
    )
    """)

    # ATTENDANCE
    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        login_time TEXT
    )
    """)

    conn.commit()
    conn.close()
