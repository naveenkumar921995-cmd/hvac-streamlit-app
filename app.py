import streamlit as st
import pandas as pd
import sqlite3
import os
import bcrypt
from datetime import datetime, date
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="DLF Cyber Park IFM", layout="wide")

# -------------------------------
# DLF CORPORATE THEME
# -------------------------------
st.markdown("""
<style>
body {
    background-color: #0d1b2a;
}
.stApp {
    background-color: #0d1b2a;
    color: white;
}
h1, h2, h3 {
    color: #d4af37;
}
div[data-testid="metric-container"] {
    background-color: #1b263b;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #d4af37;
}
.sidebar .sidebar-content {
    background-color: #1b263b;
}
</style>
""", unsafe_allow_html=True)

DB_NAME = "cyberpark.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# -------------------------------
# DATABASE TABLES
# -------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_name TEXT,
    department TEXT,
    health TEXT DEFAULT 'OK'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

conn.commit()

# -------------------------------
# AUTO CREATE ADMIN
# -------------------------------
def create_admin():
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                       ("admin", hashed, "Admin"))
        conn.commit()

create_admin()

# -------------------------------
# SMART DEPARTMENT DETECTION
# -------------------------------
def detect_department(name):
    name = name.lower()
    if any(x in name for x in ["ahu","chiller","hvac"]):
        return "HVAC"
    elif any(x in name for x in ["dg","generator"]):
        return "DG"
    elif "stp" in name:
        return "STP"
    elif "wtp" in name:
        return "WTP"
    elif "lift" in name:
        return "Lifts"
    elif "fire" in name:
        return "Fire Fighting"
    elif "cctv" in name:
        return "CCTV"
    elif "bms" in name:
        return "BMS"
    elif any(x in name for x in ["panel","electrical"]):
        return "Electrical"
    elif "vent" in name:
        return "Ventilation"
    elif "facade" in name:
        return "Facade"
    else:
        return "General"

# -------------------------------
# FIXED ASSET IMPORT
# -------------------------------
def import_assets():
    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        if os.path.exists("Asset_cyberpark.xlsx"):
            df = pd.read_excel("Asset_cyberpark.xlsx")

            # Remove completely empty columns
            df = df.dropna(axis=1, how='all')

            # Auto-detect name column
            name_col = None
            for col in df.columns:
                if any(word in col.lower() for word in ["equipment","asset","name"]):
                    name_col = col
                    break

            if name_col is None:
                name_col = df.columns[1]  # fallback

            for asset in df[name_col].dropna():
                dept = detect_department(str(asset))
                cursor.execute("INSERT INTO assets (asset_name, department) VALUES (?,?)",
                               (str(asset), dept))

            conn.commit()

import_assets()

# -------------------------------
# LOGIN
# -------------------------------
st.sidebar.title("DLF Cyber Park Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if user and bcrypt.checkpw(password.encode(), user[0]):
        st.session_state["user"] = username
        st.session_state["role"] = user[1]
    else:
        st.sidebar.error("Invalid Credentials")

if "user" not in st.session_state:
    st.stop()

st.sidebar.success(f"{st.session_state['user']} ({st.session_state['role']})")

menu = st.sidebar.radio("Navigation", [
    "Executive Dashboard",
    "All Assets Wall"
])

# -------------------------------
# EXECUTIVE DASHBOARD
# -------------------------------
if menu == "Executive Dashboard":

    st.title("DLF Cyber Park – Executive Command Center")

    df = pd.read_sql("SELECT * FROM assets", conn)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", len(df))
    col2.metric("Departments", df["department"].nunique())
    col3.metric("Healthy Assets", len(df[df["health"]=="OK"]))

    fig = px.pie(df, names="department",
                 color_discrete_sequence=["#d4af37","#f4d35e","#ee964b",
                                          "#0d3b66","#faf0ca","#3d5a80"])
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# LIVE WALL
# -------------------------------
elif menu == "All Assets Wall":

    st.title("All Systems Live Wall")

    df = pd.read_sql("SELECT asset_name, department, health FROM assets", conn)

    st.dataframe(df, use_container_width=True)
