import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
from datetime import datetime
import numpy as np

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="DLF Cyber Park – Enterprise Control Room V5",
    layout="wide"
)

# ===============================
# ULTRA DARK DLF THEME
# ===============================
st.markdown("""
<style>
body { background-color: #0b0f1a; color: white; }
h1, h2, h3 { color: #00c6ff; }
.stMetric {
    background: linear-gradient(145deg,#141c2f,#1c2333);
    padding: 15px;
    border-radius: 12px;
}
.sidebar .sidebar-content {
    background-color: #111827;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# DATABASE
# ===============================
conn = sqlite3.connect("enterprise_v5.db", check_same_thread=False)
cursor = conn.cursor()

# ===============================
# HASH PASSWORD
# ===============================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ===============================
# CREATE TABLES
# ===============================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY,
username TEXT UNIQUE,
password TEXT,
role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS assets (
id INTEGER PRIMARY KEY,
name TEXT,
department TEXT,
location TEXT,
health TEXT,
amc_end TEXT,
breakdowns INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS energy (
id INTEGER PRIMARY KEY,
asset TEXT,
kwh REAL,
cost REAL,
date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS finance (
id INTEGER PRIMARY KEY,
department TEXT,
budget REAL,
expense REAL,
month TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vendor (
id INTEGER PRIMARY KEY,
vendor_name TEXT,
response_days INTEGER,
repeat_issues INTEGER
)
""")

conn.commit()

# ===============================
# DEFAULT USERS
# ===============================
def create_users():
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

create_users()

# ===============================
# LOGIN
# ===============================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("DLF Enterprise Control Room – Secure Login")

    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (user, hash_password(pwd)))
        if cursor.fetchone():
            st.session_state.login = True
            st.session_state.username = user
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# ===============================
# SIDEBAR
# ===============================
st.sidebar.success(f"Logged in as: {st.session_state.username}")

menu = st.sidebar.radio("Navigation", [
    "Executive Dashboard",
    "Assets",
    "Energy Intelligence",
    "Finance Intelligence",
    "Vendor Intelligence",
    "Control Room"
])

# ===============================
# AI ENGINE FUNCTIONS
# ===============================

def predictive_risk(asset_row):
    risk = 0
    if asset_row["health"] == "Critical":
        risk += 40
    if asset_row["breakdowns"] > 3:
        risk += 30
    if pd.to_datetime(asset_row["amc_end"]) < pd.Timestamp.now():
        risk += 20
    return min(risk,100)

def energy_anomaly(df):
    if df.empty:
        return 0
    avg = df["kwh"].mean()
    latest = df["kwh"].iloc[-1]
    if latest > avg * 1.3:
        return "Critical"
    elif latest > avg * 1.1:
        return "Warning"
    else:
        return "Normal"

def site_kpi():
    assets = pd.read_sql("SELECT * FROM assets", conn)
    if assets.empty:
        return 100
    risk_scores = assets.apply(predictive_risk, axis=1)
    avg_risk = risk_scores.mean()
    return max(100 - avg_risk,0)

# ===============================
# EXECUTIVE DASHBOARD
# ===============================
if menu == "Executive Dashboard":

    st.title("Enterprise AI Executive Dashboard")

    col1,col2,col3 = st.columns(3)

    total_assets = pd.read_sql("SELECT COUNT(*) as c FROM assets", conn)["c"][0]
    col1.metric("Total Assets", total_assets)

    col2.metric("Site KPI Score", round(site_kpi(),1))

    energy_df = pd.read_sql("SELECT * FROM energy", conn)
    anomaly = energy_anomaly(energy_df)
    col3.metric("Energy Status", anomaly)

# ===============================
# ASSETS
# ===============================
elif menu == "Assets":

    st.title("Asset Management")

    with st.form("asset_form"):
        name = st.text_input("Asset Name")
        dept = st.selectbox("Department",
            ["HVAC","DG","Electrical","STP","WTP","Lifts",
             "CCTV","Fire","Facade","BMS"])
        loc = st.text_input("Location")
        health = st.selectbox("Health",["OK","Attention","Critical"])
        amc = st.date_input("AMC End Date")
        breakdown = st.number_input("Breakdown Count",0)

        if st.form_submit_button("Add Asset"):
            cursor.execute("""
            INSERT INTO assets (name,department,location,health,amc_end,breakdowns)
            VALUES (?,?,?,?,?,?)
            """,(name,dept,loc,health,str(amc),breakdown))
            conn.commit()
            st.success("Asset Added")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        df["Risk Score"] = df.apply(predictive_risk, axis=1)
        st.dataframe(df)

# ===============================
# ENERGY INTELLIGENCE
# ===============================
elif menu == "Energy Intelligence":

    st.title("Energy + BTU AI Engine")

    with st.form("energy_form"):
        asset = st.text_input("Asset")
        kwh = st.number_input("kWh",0.0)
        cost = st.number_input("Cost",0.0)

        if st.form_submit_button("Add Energy"):
            cursor.execute("""
            INSERT INTO energy (asset,kwh,cost,date)
            VALUES (?,?,?,?)
            """,(asset,kwh,cost,str(datetime.now())))
            conn.commit()
            st.success("Energy Logged")

    df = pd.read_sql("SELECT * FROM energy", conn)

    if not df.empty:
        df["BTU"] = df["kwh"] * 3412
        st.dataframe(df)

        st.metric("Energy Anomaly Status", energy_anomaly(df))

# ===============================
# FINANCE INTELLIGENCE
# ===============================
elif menu == "Finance Intelligence":

    st.title("Budget vs P&L Intelligence")

    with st.form("finance_form"):
        dept = st.text_input("Department")
        budget = st.number_input("Budget",0.0)
        expense = st.number_input("Expense",0.0)
        month = st.text_input("Month")

        if st.form_submit_button("Add Finance"):
            cursor.execute("""
            INSERT INTO finance (department,budget,expense,month)
            VALUES (?,?,?,?)
            """,(dept,budget,expense,month))
            conn.commit()
            st.success("Finance Added")

    df = pd.read_sql("SELECT * FROM finance", conn)
    if not df.empty:
        df["Variance"] = df["budget"] - df["expense"]
        st.dataframe(df)

# ===============================
# VENDOR INTELLIGENCE
# ===============================
elif menu == "Vendor Intelligence":

    st.title("Vendor Performance Scoring")

    with st.form("vendor_form"):
        name = st.text_input("Vendor Name")
        response = st.number_input("Avg Response Days",0)
        repeat = st.number_input("Repeat Issues",0)

        if st.form_submit_button("Add Vendor"):
            cursor.execute("""
            INSERT INTO vendor (vendor_name,response_days,repeat_issues)
            VALUES (?,?,?)
            """,(name,response,repeat))
            conn.commit()
            st.success("Vendor Added")

    df = pd.read_sql("SELECT * FROM vendor", conn)

    if not df.empty:
        df["Performance Score"] = 100 - (df["response_days"]*5 + df["repeat_issues"]*10)
        st.dataframe(df)

# ===============================
# CONTROL ROOM
# ===============================
elif menu == "Control Room":

    st.title("DLF LIVE CONTROL ROOM VIEW")

    df = pd.read_sql("SELECT name,department,health FROM assets", conn)
    st.dataframe(df)

