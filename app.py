import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="DLF Cyber Park – Enterprise Control Room",
                   layout="wide")

# =========================
# DARK CORPORATE UI
# =========================
st.markdown("""
<style>
body { background-color:#0e1117; color:white; }
.stMetric { background-color:#1c1f26; padding:15px; border-radius:10px; }
h1,h2,h3 { color:#00BFFF; }
</style>
""", unsafe_allow_html=True)

# =========================
# DATABASE CONNECTION
# =========================
conn = sqlite3.connect("enterprise.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# PASSWORD HASHING
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# CREATE TABLES
# =========================
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
name TEXT,
location TEXT,
department TEXT,
health TEXT,
amc_end TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS energy (
id INTEGER PRIMARY KEY AUTOINCREMENT,
asset_name TEXT,
kwh REAL,
cost REAL,
date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
login_time TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS finance (
id INTEGER PRIMARY KEY AUTOINCREMENT,
department TEXT,
budget REAL,
expense REAL,
month TEXT
)
""")

conn.commit()

# =========================
# DEFAULT USERS
# =========================
def create_default_users():
    users = [
        ("admin", hash_password("Admin@123"), "Admin"),
        ("manager", hash_password("Manager@123"), "Manager"),
        ("engineer", hash_password("Engineer@123"), "Engineer")
    ]
    for u in users:
        try:
            cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", u)
        except:
            pass
    conn.commit()

create_default_users()

# =========================
# LOGIN
# =========================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("DLF Cyber Park – Enterprise Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (username, hash_password(password)))
        user = cursor.fetchone()

        if user:
            st.session_state.login = True
            st.session_state.username = username
            st.session_state.role = user[3]
            cursor.execute("INSERT INTO attendance (username,login_time) VALUES (?,?)",
                           (username, str(datetime.now())))
            conn.commit()
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.success(f"{st.session_state.username} ({st.session_state.role})")

menu = st.sidebar.radio("Navigation", [
    "Executive Dashboard",
    "Assets",
    "Energy + BTU",
    "Finance",
    "Reports",
    "Control Room"
])

# =========================
# KPI ENGINE
# =========================
def calculate_kpi():
    total = pd.read_sql("SELECT COUNT(*) as c FROM assets", conn)["c"][0]
    critical = pd.read_sql(
        "SELECT COUNT(*) as c FROM assets WHERE health='Critical'", conn)["c"][0]
    expired = pd.read_sql(
        "SELECT COUNT(*) as c FROM assets WHERE amc_end < date('now')", conn)["c"][0]

    score = 100 - (critical*5) - (expired*3)
    return max(score,0)

# =========================
# EXECUTIVE DASHBOARD
# =========================
if menu == "Executive Dashboard":
    st.title("Enterprise Executive Dashboard")

    col1,col2,col3,col4 = st.columns(4)

    total_assets = pd.read_sql("SELECT COUNT(*) as c FROM assets", conn)["c"][0]
    col1.metric("Total Assets", total_assets)

    kpi = calculate_kpi()
    col2.metric("Site KPI Score", f"{kpi}/100")

    energy_sum = pd.read_sql("SELECT SUM(kwh) as s FROM energy", conn)["s"][0]
    col3.metric("Total kWh", 0 if energy_sum is None else round(energy_sum,2))

    finance = pd.read_sql("SELECT SUM(budget-expense) as v FROM finance", conn)["v"][0]
    col4.metric("Budget Variance", 0 if finance is None else round(finance,2))

# =========================
# ASSET MANAGEMENT
# =========================
elif menu == "Assets":
    st.title("Asset Management")

    with st.form("asset_form"):
        name = st.text_input("Asset Name")
        location = st.text_input("Location")
        department = st.selectbox("Department",
            ["HVAC","DG","Electrical","STP","WTP","Lifts","CCTV","Fire","Facade","BMS"])
        health = st.selectbox("Health",["OK","Attention","Critical"])
        amc_end = st.date_input("AMC End Date")

        if st.form_submit_button("Add Asset"):
            cursor.execute(
                "INSERT INTO assets (name,location,department,health,amc_end) VALUES (?,?,?,?,?)",
                (name,location,department,health,str(amc_end)))
            conn.commit()
            st.success("Asset Added")

    st.dataframe(pd.read_sql("SELECT * FROM assets", conn))

# =========================
# ENERGY + BTU
# =========================
elif menu == "Energy + BTU":
    st.title("Energy & BTU Tracking")

    with st.form("energy_form"):
        asset = st.text_input("Asset Name")
        kwh = st.number_input("kWh",0.0)
        cost = st.number_input("Cost",0.0)

        if st.form_submit_button("Add Energy"):
            cursor.execute(
                "INSERT INTO energy (asset_name,kwh,cost,date) VALUES (?,?,?,?)",
                (asset,kwh,cost,str(datetime.now())))
            conn.commit()
            st.success("Energy Logged")

    df = pd.read_sql("SELECT * FROM energy", conn)
    if not df.empty:
        df["BTU"] = df["kwh"] * 3412
        st.dataframe(df)

# =========================
# FINANCE
# =========================
elif menu == "Finance":
    st.title("Budget vs P&L")

    with st.form("finance_form"):
        dept = st.text_input("Department")
        budget = st.number_input("Budget",0.0)
        expense = st.number_input("Expense",0.0)
        month = st.text_input("Month")

        if st.form_submit_button("Add Finance Data"):
            cursor.execute(
                "INSERT INTO finance (department,budget,expense,month) VALUES (?,?,?,?)",
                (dept,budget,expense,month))
            conn.commit()
            st.success("Finance Data Added")

    st.dataframe(pd.read_sql("SELECT *, (budget-expense) as Variance FROM finance", conn))

# =========================
# REPORTS
# =========================
elif menu == "Reports":
    st.title("Management Report")

    if st.button("Generate PDF Report"):
        doc = SimpleDocTemplate("DLF_Report.pdf")
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("DLF Cyber Park Executive Report",
                                  styles["Heading1"]))
        elements.append(Spacer(1,0.5*inch))
        elements.append(Paragraph(f"KPI Score: {calculate_kpi()}",
                                  styles["Normal"]))

        doc.build(elements)
        st.success("Report Generated")

# =========================
# CONTROL ROOM
# =========================
elif menu == "Control Room":
    st.title("DLF CYBER PARK – LIVE CONTROL ROOM")
    df = pd.read_sql("SELECT name,department,health FROM assets", conn)
    st.dataframe(df)

# =========================
# POWER BI EXPORT
# =========================
st.sidebar.markdown("---")
if st.sidebar.button("Export Data for Power BI"):
    pd.read_sql("SELECT * FROM assets", conn).to_csv("powerbi_export.csv",index=False)
    st.sidebar.success("Exported")
