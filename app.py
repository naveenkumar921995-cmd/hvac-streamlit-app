import streamlit as st
import pandas as pd
import sqlite3
import os
import bcrypt
from datetime import datetime, date
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="DLF Cyber Park IFM", layout="wide")

DB_NAME = "cyberpark.db"

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

# --------------------------------------------------
# CREATE TABLES
# --------------------------------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_name TEXT,
    department TEXT,
    health TEXT DEFAULT 'OK',
    amc_end DATE,
    compliance_end DATE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_name TEXT,
    log_date DATE,
    kwh REAL,
    btu REAL,
    cost REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    login_time TEXT
)
""")

conn.commit()

# --------------------------------------------------
# AUTO CREATE ADMIN
# --------------------------------------------------
def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                       ("admin", hashed, "Admin"))
        conn.commit()

create_default_admin()

# --------------------------------------------------
# AUTO IMPORT ASSET FILE
# --------------------------------------------------
def detect_department(name):
    name = name.lower()
    if "ahu" in name or "chiller" in name or "hvac" in name:
        return "HVAC"
    elif "dg" in name or "generator" in name:
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
    elif "electrical" in name or "panel" in name:
        return "Electrical"
    elif "vent" in name:
        return "Ventilation"
    elif "facade" in name:
        return "Facade"
    else:
        return "General"

def import_assets():
    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        if os.path.exists("Asset_cyberpark.xlsx"):
            df = pd.read_excel("Asset_cyberpark.xlsx")
            col = df.columns[0]
            for asset in df[col].dropna():
                dept = detect_department(str(asset))
                cursor.execute("INSERT INTO assets (asset_name, department) VALUES (?,?)",
                               (str(asset), dept))
            conn.commit()

import_assets()

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        if user and bcrypt.checkpw(password.encode(), user[0]):
            st.session_state["user"] = username
            st.session_state["role"] = user[1]
            cursor.execute("INSERT INTO attendance (username, login_time) VALUES (?,?)",
                           (username, str(datetime.now())))
            conn.commit()
        else:
            st.sidebar.error("Invalid credentials")

if "user" not in st.session_state:
    login()
    st.stop()

st.sidebar.success(f"{st.session_state['user']} ({st.session_state['role']})")

# --------------------------------------------------
# MENU
# --------------------------------------------------
menu = st.sidebar.radio("Navigation", [
    "Executive Dashboard",
    "All Assets Live Wall",
    "Energy & BTU",
    "AMC / Compliance",
    "Attendance",
    "Monthly PDF Report"
])

# --------------------------------------------------
# EXECUTIVE DASHBOARD
# --------------------------------------------------
if menu == "Executive Dashboard":
    st.title("DLF Cyber Park – Executive Dashboard")

    assets_df = pd.read_sql("SELECT * FROM assets", conn)
    energy_df = pd.read_sql("SELECT * FROM energy_logs", conn)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", len(assets_df))
    col2.metric("Departments", assets_df["department"].nunique())
    col3.metric("Attention Assets",
                len(assets_df[assets_df["health"] != "OK"]))

    fig = px.pie(assets_df, names="department", title="Department Distribution")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# LIVE WALL
# --------------------------------------------------
elif menu == "All Assets Live Wall":
    st.title("All Departments – Live Asset Wall")
    df = pd.read_sql("SELECT asset_name, department, health FROM assets", conn)
    st.dataframe(df)

# --------------------------------------------------
# ENERGY
# --------------------------------------------------
elif menu == "Energy & BTU":
    st.title("Energy & BTU Management")

    asset_list = pd.read_sql("SELECT asset_name FROM assets", conn)["asset_name"].tolist()

    with st.form("energy"):
        asset = st.selectbox("Asset", asset_list)
        kwh = st.number_input("kWh")
        btu = st.number_input("BTU")
        cost = st.number_input("Cost")
        submit = st.form_submit_button("Submit")

    if submit:
        cursor.execute("""
        INSERT INTO energy_logs (asset_name, log_date, kwh, btu, cost)
        VALUES (?,?,?,?,?)
        """, (asset, str(date.today()), kwh, btu, cost))
        conn.commit()
        st.success("Energy log saved")

    df = pd.read_sql("SELECT * FROM energy_logs", conn)
    if not df.empty:
        fig = px.bar(df, x="asset_name", y="kwh", title="Energy Consumption")
        st.plotly_chart(fig)

# --------------------------------------------------
# AMC
# --------------------------------------------------
elif menu == "AMC / Compliance":
    st.title("AMC & Compliance Tracking")

    df = pd.read_sql("SELECT * FROM assets", conn)

    asset = st.selectbox("Asset", df["asset_name"])
    amc_date = st.date_input("AMC End Date")
    comp_date = st.date_input("Compliance End Date")

    if st.button("Update"):
        cursor.execute("""
        UPDATE assets SET amc_end=?, compliance_end=? WHERE asset_name=?
        """, (str(amc_date), str(comp_date), asset))
        conn.commit()
        st.success("Updated")

    today = str(date.today())
    expiring = df[(df["amc_end"] < today) | (df["compliance_end"] < today)]
    st.subheader("Expiring / Expired Assets")
    st.dataframe(expiring)

# --------------------------------------------------
# ATTENDANCE
# --------------------------------------------------
elif menu == "Attendance":
    st.title("Attendance Log")
    df = pd.read_sql("SELECT * FROM attendance", conn)
    st.dataframe(df)

# --------------------------------------------------
# PDF REPORT
# --------------------------------------------------
elif menu == "Monthly PDF Report":
    st.title("Generate Monthly Report")

    if st.button("Generate PDF"):
        doc = SimpleDocTemplate("Monthly_Report.pdf")
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("DLF Cyber Park Monthly Report", styles["Title"]))
        elements.append(Spacer(1, 20))

        assets_df = pd.read_sql("SELECT * FROM assets", conn)
        elements.append(Paragraph(f"Total Assets: {len(assets_df)}", styles["Normal"]))

        doc.build(elements)

        with open("Monthly_Report.pdf", "rb") as f:
            st.download_button("Download Report", f, "Monthly_Report.pdf")

