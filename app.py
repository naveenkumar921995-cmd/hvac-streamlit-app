import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime, date
import hashlib

# ---------------- CONFIG ---------------- #
st.set_page_config(layout="wide", page_title="DLF Cyber Park – Enterprise Control Room V3")

DB = "enterprise.db"
EXCEL_FILE = "Asset_cyberpark.xlsx"

# ---------------- DLF THEME ---------------- #
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#071a2d,#0b2a45);}
h1,h2,h3 {color:white;}
.metric-card {
background:#0f3a5d;padding:20px;border-radius:12px;color:white;
box-shadow:0 0 20px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# ---------------- DB INIT ---------------- #
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS assets(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        location TEXT,
        department TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS energy(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        kwh REAL,
        date TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS amc(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT,
        vendor TEXT,
        expiry_date TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee TEXT,
        login_time TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------------- AUTO CLASSIFICATION ---------------- #
def classify(name):
    n = name.upper()
    if "AHU" in n or "FCU" in n or "CHILLER" in n:
        return "HVAC"
    elif "DG" in n:
        return "DG"
    elif "STP" in n:
        return "STP"
    elif "WTP" in n:
        return "WTP"
    elif "LIFT" in n:
        return "LIFTS"
    elif "CCTV" in n:
        return "CCTV"
    elif "FIRE" in n:
        return "FIRE FIGHTING"
    elif "PANEL" in n or "TRANSFORMER" in n:
        return "ELECTRICAL"
    elif "BMS" in n:
        return "BMS"
    elif "FACADE" in n:
        return "FACADE"
    elif "VENT" in n:
        return "VENTILATION"
    else:
        return "GENERAL"

# ---------------- FIRST RUN LOAD ---------------- #
def load_excel_once():
    conn = sqlite3.connect(DB)
    existing = pd.read_sql("SELECT * FROM assets", conn)

    if existing.empty and os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)

        # Clean column names properly
        df.columns = df.columns.str.strip()

        # Use exact correct names from your file
        if "Asset Name" not in df.columns:
            st.error("Column 'Asset Name' not found in Excel")
            st.stop()

        asset_col = "Asset Name"

        if "Room (if Applicable)" in df.columns:
            location_col = "Room (if Applicable)"
        else:
            location_col = None

        df = df[[asset_col]].copy()
        df.rename(columns={asset_col: "asset_name"}, inplace=True)

        if location_col:
            df["location"] = pd.read_excel(EXCEL_FILE)[location_col]
        else:
            df["location"] = "Not Specified"

        df["department"] = df["asset_name"].apply(classify)

        df[["asset_name", "location", "department"]].to_sql(
            "assets", conn, if_exists="append", index=False
        )

    conn.close()

    if existing.empty and os.path.exists(EXCEL_FILE):
        df = pd.read_excel(EXCEL_FILE)
        df.columns = df.columns.str.strip()

        df = df[["Asset Name","Room(if applicable)"]]
        df.rename(columns={
            "Asset Name":"asset_name",
            "Room(if applicable)":"location"
        }, inplace=True)

        df["department"] = df["asset_name"].apply(classify)
        df.to_sql("assets", conn, if_exists="append", index=False)

    conn.close()

load_excel_once()

# ---------------- LOGIN (HASHED) ---------------- #
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

USERS = {"admin": hash_pass("Admin@123")}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("DLF Cyber Park – Enterprise Control Room V3")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u] == hash_pass(p):
            st.session_state.login = True
            st.success("Login Successful")
        else:
            st.error("Invalid Credentials")
    st.stop()

# ---------------- LOAD DATA ---------------- #
conn = sqlite3.connect(DB)
assets = pd.read_sql("SELECT * FROM assets", conn)
energy = pd.read_sql("SELECT * FROM energy", conn)
amc = pd.read_sql("SELECT * FROM amc", conn)
attendance = pd.read_sql("SELECT * FROM attendance", conn)

# ---------------- EXECUTIVE DASHBOARD ---------------- #
st.title("🏢 Executive Command Dashboard")

col1,col2,col3,col4 = st.columns(4)

total_assets = len(assets)
total_energy = energy["kwh"].sum() if not energy.empty else 0
total_btu = total_energy * 3412
active_amc = len(amc)

col1.metric("Total Assets", total_assets)
col2.metric("Total Energy (kWh)", round(total_energy,2))
col3.metric("Total BTU", round(total_btu,2))
col4.metric("Active AMC", active_amc)

st.subheader("Department Distribution")
st.bar_chart(assets["department"].value_counts())

# ---------------- ENERGY ENTRY ---------------- #
st.subheader("Energy Entry")
if not assets.empty:
    asset_select = st.selectbox("Select Asset", assets["asset_name"])
    kwh = st.number_input("Enter kWh", min_value=0.0)

    if st.button("Save Energy"):
        pd.DataFrame({
            "asset_name":[asset_select],
            "kwh":[kwh],
            "date":[date.today()]
        }).to_sql("energy", conn, if_exists="append", index=False)
        st.success("Energy Saved")

# ---------------- AMC TRACKING ---------------- #
st.subheader("AMC Entry")
if not assets.empty:
    asset_select2 = st.selectbox("Asset for AMC", assets["asset_name"], key="amc")
    vendor = st.text_input("Vendor Name")
    expiry = st.date_input("Expiry Date")

    if st.button("Save AMC"):
        pd.DataFrame({
            "asset_name":[asset_select2],
            "vendor":[vendor],
            "expiry_date":[expiry]
        }).to_sql("amc", conn, if_exists="append", index=False)
        st.success("AMC Saved")

# ---------------- AMC ALERT ---------------- #
st.subheader("AMC Expiry Alerts")
if not amc.empty:
    amc["expiry_date"] = pd.to_datetime(amc["expiry_date"])
    alert = amc[amc["expiry_date"] < pd.Timestamp.today() + pd.Timedelta(days=30)]
    st.dataframe(alert)

# ---------------- ATTENDANCE ---------------- #
st.subheader("Attendance")
if st.button("Mark Attendance"):
    pd.DataFrame({
        "employee":["admin"],
        "login_time":[datetime.now()]
    }).to_sql("attendance", conn, if_exists="append", index=False)
    st.success("Attendance Marked")

st.dataframe(attendance)

conn.close()
