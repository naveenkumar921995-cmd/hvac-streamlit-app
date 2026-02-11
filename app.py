import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="DLF Cyber Park - IFM Platform", layout="wide")

DB_NAME = "dlf_ifm.db"

DEPARTMENTS = [
    "HVAC","DG","Electrical","STP","WTP","Ventilation",
    "Lifts","CCTV","BMS","Fire Fighting","Facade","Compliance"
]

# ---------------- DATABASE ---------------- #
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

# Create Tables
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
    department TEXT,
    asset_id TEXT,
    asset_name TEXT,
    location TEXT,
    health TEXT,
    amc_vendor TEXT,
    amc_end DATE,
    compliance_end DATE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department TEXT,
    asset_id TEXT,
    log_date DATE,
    kwh REAL,
    btu REAL,
    cost_per_kwh REAL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS work_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department TEXT,
    asset_id TEXT,
    engineer TEXT,
    log_date DATE,
    work_type TEXT,
    remarks TEXT,
    status TEXT
)
""")

conn.commit()

# Default Admin
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                   ("admin","admin123","Admin"))
    conn.commit()

# ---------------- LOGIN ---------------- #
st.sidebar.title("🔐 Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                   (username,password))
    user = cursor.fetchone()
    if user:
        st.session_state["logged"] = True
        st.session_state["role"] = user[3]
        st.session_state["user"] = user[1]
    else:
        st.sidebar.error("Invalid Credentials")

if "logged" not in st.session_state:
    st.stop()

st.sidebar.success(f"Welcome {st.session_state['user']}")

menu = st.sidebar.radio("Navigation",[
    "Live Wall Dashboard",
    "Asset Management",
    "Energy Monitoring",
    "Work Logs",
    "AMC & Compliance Alerts"
])

# ==========================================================
# 1️⃣ LIVE WALL DASHBOARD
# ==========================================================
if menu == "Live Wall Dashboard":
    st.title("🏢 All Departments - Live Command Center")

    assets_df = pd.read_sql("SELECT * FROM assets", conn)
    energy_df = pd.read_sql("SELECT * FROM energy_logs", conn)

    col1,col2,col3,col4 = st.columns(4)

    col1.metric("Total Assets", len(assets_df))
    col2.metric("Attention Required",
                len(assets_df[assets_df["health"]=="Attention"]))
    col3.metric("Total Energy (kWh)",
                round(energy_df["kwh"].sum() if not energy_df.empty else 0,2))
    col4.metric("Total Cost ₹",
                round((energy_df["kwh"]*energy_df["cost_per_kwh"]).sum()
                      if not energy_df.empty else 0,2))

    st.subheader("Department Summary")

    if not assets_df.empty:
        summary = assets_df.groupby("department")["asset_id"].count()
        st.bar_chart(summary)

    st.dataframe(assets_df, use_container_width=True)

# ==========================================================
# 2️⃣ ASSET MANAGEMENT
# ==========================================================
elif menu == "Asset Management":
    st.title("Asset Master Management")

    department = st.selectbox("Department", DEPARTMENTS)

    with st.form("asset_form"):
        asset_id = st.text_input("Asset ID")
        asset_name = st.text_input("Asset Name")
        location = st.text_input("Location")
        health = st.selectbox("Health",["OK","Attention"])
        vendor = st.text_input("AMC Vendor")
        amc_end = st.date_input("AMC End Date")
        compliance_end = st.date_input("Compliance Expiry Date")
        submit = st.form_submit_button("Save Asset")

    if submit:
        cursor.execute("""
        INSERT INTO assets
        (department,asset_id,asset_name,location,health,
         amc_vendor,amc_end,compliance_end)
        VALUES (?,?,?,?,?,?,?,?)
        """,(department,asset_id,asset_name,location,
             health,vendor,amc_end,compliance_end))
        conn.commit()
        st.success("Asset Added Successfully")

    df = pd.read_sql("SELECT * FROM assets WHERE department=?",
                     conn, params=(department,))
    st.dataframe(df, use_container_width=True)

# ==========================================================
# 3️⃣ ENERGY MONITORING
# ==========================================================
elif menu == "Energy Monitoring":
    st.title("Energy + BTU Monitoring")

    department = st.selectbox("Department", DEPARTMENTS)

    assets_df = pd.read_sql(
        "SELECT asset_id FROM assets WHERE department=?",
        conn, params=(department,)
    )

    if not assets_df.empty:
        asset_id = st.selectbox("Asset", assets_df["asset_id"])

        with st.form("energy_form"):
            kwh = st.number_input("kWh", min_value=0.0)
            btu = st.number_input("BTU", min_value=0.0)
            cost = st.number_input("Cost per kWh ₹", min_value=0.0)
            submit = st.form_submit_button("Submit")

        if submit:
            cursor.execute("""
            INSERT INTO energy_logs
            (department,asset_id,log_date,kwh,btu,cost_per_kwh)
            VALUES (?,?,?,?,?,?)
            """,(department,asset_id,date.today(),kwh,btu,cost))
            conn.commit()
            st.success("Energy Log Added")

    df = pd.read_sql("SELECT * FROM energy_logs", conn)
    st.dataframe(df, use_container_width=True)

# ==========================================================
# 4️⃣ WORK LOGS
# ==========================================================
elif menu == "Work Logs":
    st.title("Daily Work Logs")

    department = st.selectbox("Department", DEPARTMENTS)

    assets_df = pd.read_sql(
        "SELECT asset_id FROM assets WHERE department=?",
        conn, params=(department,)
    )

    if not assets_df.empty:
        asset_id = st.selectbox("Asset", assets_df["asset_id"])
        work_type = st.selectbox("Work Type",
                                 ["Routine","Preventive","Breakdown"])
        remarks = st.text_area("Remarks")
        status = st.selectbox("Status",["Closed","Open"])

        if st.button("Submit Log"):
            cursor.execute("""
            INSERT INTO work_logs
            (department,asset_id,engineer,log_date,work_type,remarks,status)
            VALUES (?,?,?,?,?,?,?)
            """,(department,asset_id,
                 st.session_state["user"],
                 date.today(),work_type,remarks,status))
            conn.commit()
            st.success("Work Log Saved")

    df = pd.read_sql("SELECT * FROM work_logs", conn)
    st.dataframe(df, use_container_width=True)

# ==========================================================
# 5️⃣ AMC & COMPLIANCE ALERTS
# ==========================================================
elif menu == "AMC & Compliance Alerts":
    st.title("AMC & Compliance Expiry Alerts")

    today = date.today()

    assets_df = pd.read_sql("SELECT * FROM assets", conn)

    if not assets_df.empty:
        assets_df["amc_end"] = pd.to_datetime(assets_df["amc_end"])
        assets_df["compliance_end"] = pd.to_datetime(
            assets_df["compliance_end"])

        amc_alert = assets_df[
            assets_df["amc_end"] <= pd.Timestamp(today)
        ]

        compliance_alert = assets_df[
            assets_df["compliance_end"] <= pd.Timestamp(today)
        ]

        if not amc_alert.empty:
            st.error("⚠ AMC Expired / Due")
            st.dataframe(amc_alert)

        if not compliance_alert.empty:
            st.error("⚠ Compliance Expired / Due")
            st.dataframe(compliance_alert)

        if amc_alert.empty and compliance_alert.empty:
            st.success("All AMC & Compliance Valid")

