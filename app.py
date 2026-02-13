import os
import pandas as pd
import sqlite3

DB_FILE = "enterprise_v6.db"
EXCEL_FILE = "DLF_Enterprise_Asset_Master_Template.xlsx"

def initialize_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        department TEXT,
        location TEXT,
        capacity TEXT,
        energy_kwh REAL,
        amc_expiry DATE
    )
    """)

    conn.commit()
    conn.close()

def auto_import_excel():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE)
            conn = sqlite3.connect(DB_FILE)
            df.to_sql("assets", conn, if_exists="replace", index=False)
            conn.close()

initialize_database()
auto_import_excel()

import streamlit as st
from PIL import Image

# ===== HEADER WITH LOGOS =====
col1, col2, col3 = st.columns([1,6,1])

with col1:
    st.image("dlf_logo.png", width=120)

with col2:
    st.markdown(
        "<h1 style='text-align:center; color:#00F0FF;'>DLF ENTERPRISE CONTROL ROOM V6</h1>",
        unsafe_allow_html=True
    )

with col3:
    st.image("lnp_logo.png", width=120)

st.markdown("---")

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import hashlib
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import os

# ==============================
# PAGE CONFIG
# ==============================
st.markdown("""
<style>
.stApp {
    background-color: #0A192F;
    color: #E6F1FF;
}
h1, h2, h3 {
    color: #00F0FF;
}
div[data-testid="stMetric"] {
    background-color: #112240;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(
    page_title="DLF Enterprise Control Room V6",
    layout="wide",
    page_icon="🏢"
)

# ==============================
# ULTRA DARK BOARDROOM THEME
# ==============================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg,#0b0f1a,#111827);
    color:white;
}
.big-card {
    background: rgba(20,25,40,0.9);
    padding:20px;
    border-radius:15px;
    box-shadow:0 0 20px rgba(0,198,255,0.2);
}
.metric-card {
    background: linear-gradient(145deg,#111827,#1f2937);
    padding:15px;
    border-radius:12px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# DATABASE
# ==============================
conn = sqlite3.connect("enterprise_v6.db", check_same_thread=False)
cursor = conn.cursor()

# ==============================
# TABLE CREATION
# ==============================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
username TEXT UNIQUE,
password TEXT,
role TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS assets(
id INTEGER PRIMARY KEY,
asset_name TEXT,
department TEXT,
location TEXT,
health TEXT,
amc_expiry TEXT,
breakdowns INTEGER)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS energy(
id INTEGER PRIMARY KEY,
asset_name TEXT,
kwh REAL,
cost REAL,
date TEXT)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS finance(
id INTEGER PRIMARY KEY,
department TEXT,
budget REAL,
expense REAL,
month TEXT)
""")

conn.commit()

# ==============================
# PASSWORD HASHING
# ==============================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def create_admin():
    try:
        cursor.execute("INSERT INTO users VALUES (NULL,?,?,?)",
                       ("admin", hash_password("Admin@123"), "Admin"))
        conn.commit()
    except:
        pass

create_admin()

# ==============================
# LOGIN SYSTEM
# ==============================
if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("DLF Enterprise Boardroom Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                       (u, hash_password(p)))
        if cursor.fetchone():
            st.session_state.login = True
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

# ==============================
# AUTO IMPORT EXCEL TEMPLATE
# ==============================
if st.sidebar.button("Import Asset Master (Excel)"):
    try:
        file = "DLF_Enterprise_Asset_Master_Template.xlsx"
        if os.path.exists(file):
            xl = pd.ExcelFile(file)
            for sheet in xl.sheet_names:
                df = xl.parse(sheet)
                for _, row in df.iterrows():
                    cursor.execute("""
                    INSERT INTO assets (asset_name,department,location,health,amc_expiry,breakdowns)
                    VALUES (?,?,?,?,?,?)
                    """,(
                        str(row.get("Asset Name","")),
                        sheet,
                        str(row.get("Location","")),
                        "OK",
                        str(datetime.now().date() + timedelta(days=365)),
                        0
                    ))
            conn.commit()
            st.success("Asset Master Imported")
        else:
            st.error("Excel file not found in repo")
    except Exception as e:
        st.error(str(e))

# ==============================
# AI ENGINES
# ==============================
def risk_score(row):
    score = 0
    if row["health"] == "Critical":
        score += 40
    if row["breakdowns"] > 2:
        score += 30
    if pd.to_datetime(row["amc_expiry"]) < pd.Timestamp.now():
        score += 20
    return min(score,100)

def site_kpi():
    df = pd.read_sql("SELECT * FROM assets", conn)
    if df.empty:
        return 100
    df["risk"] = df.apply(risk_score, axis=1)
    return max(100 - df["risk"].mean(), 0)

def energy_anomaly():
    df = pd.read_sql("SELECT * FROM energy", conn)
    if df.empty:
        return "Stable"
    avg = df["kwh"].mean()
    latest = df["kwh"].iloc[-1]
    if latest > avg * 1.3:
        return "Critical"
    elif latest > avg * 1.1:
        return "Warning"
    return "Stable"

# ==============================
# SIDEBAR MENU
# ==============================
menu = st.sidebar.radio("Navigation",[
    "Boardroom Dashboard",
    "Asset Intelligence",
    "Energy Intelligence",
    "Financial Intelligence",
    "Control Room Mode"
])

# ==============================
# BOARDROOM DASHBOARD
# ==============================
if menu == "Boardroom Dashboard":

    st.title("🏢 Executive Boardroom Intelligence")

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total Assets",
        pd.read_sql("SELECT COUNT(*) c FROM assets",conn)["c"][0])

    col2.metric("Site KPI Score", round(site_kpi(),1))

    col3.metric("Energy Status", energy_anomaly())

    finance_df = pd.read_sql("SELECT * FROM finance",conn)
    if not finance_df.empty:
        variance = (finance_df["budget"] - finance_df["expense"]).sum()
    else:
        variance = 0

    col4.metric("Budget Variance", variance)

    # Department Risk Heatmap
    df = pd.read_sql("SELECT * FROM assets", conn)
    if not df.empty:
        df["Risk"] = df.apply(risk_score, axis=1)
        dept = df.groupby("department")["Risk"].mean().reset_index()
        fig = px.bar(dept, x="department", y="Risk",
                     title="Department Risk Heat Index",
                     color="Risk",
                     color_continuous_scale="Reds")
        st.plotly_chart(fig, use_container_width=True)

# ==============================
# ASSET INTELLIGENCE
# ==============================
elif menu == "Asset Intelligence":

    st.title("Asset Risk Intelligence")

    df = pd.read_sql("SELECT * FROM assets", conn)

    if not df.empty:
        df["Risk Score"] = df.apply(risk_score, axis=1)
        st.dataframe(df)

# ==============================
# ENERGY INTELLIGENCE
# ==============================
elif menu == "Energy Intelligence":

    st.title("Energy + BTU Analytics")

    with st.form("energy"):
        a = st.text_input("Asset")
        k = st.number_input("kWh",0.0)
        c = st.number_input("Cost",0.0)
        if st.form_submit_button("Add Energy"):
            cursor.execute("INSERT INTO energy VALUES(NULL,?,?,?,?)",
                           (a,k,c,str(datetime.now())))
            conn.commit()

    df = pd.read_sql("SELECT * FROM energy", conn)

    if not df.empty:
        df["BTU"] = df["kwh"] * 3412
        fig = px.line(df, x="date", y="kwh", title="Energy Trend")
        st.plotly_chart(fig, use_container_width=True)

# ==============================
# FINANCIAL INTELLIGENCE
# ==============================
elif menu == "Financial Intelligence":

    st.title("Budget vs P&L Forecast")

    with st.form("finance"):
        d = st.text_input("Department")
        b = st.number_input("Budget",0.0)
        e = st.number_input("Expense",0.0)
        m = st.text_input("Month")
        if st.form_submit_button("Add Record"):
            cursor.execute("INSERT INTO finance VALUES(NULL,?,?,?,?)",
                           (d,b,e,m))
            conn.commit()

    df = pd.read_sql("SELECT * FROM finance", conn)
    if not df.empty:
        df["Variance"] = df["budget"] - df["expense"]
        st.dataframe(df)

# ==============================
# CONTROL ROOM MODE
# ==============================
elif menu == "Control Room Mode":

    st.title("🔴 LIVE CONTROL ROOM MODE")

    st.info("Auto Refresh Every 10 Seconds")

    placeholder = st.empty()

    while True:
        with placeholder.container():
            col1,col2 = st.columns(2)
            col1.metric("Site KPI", round(site_kpi(),1))
            col2.metric("Energy Status", energy_anomaly())
            df = pd.read_sql("SELECT asset_name,health FROM assets",conn)
            st.dataframe(df)
        time.sleep(10)
        st.rerun()
