import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import hashlib

# ---------------- CONFIG ---------------- #
st.set_page_config(layout="wide", page_title="DLF Cyber Park – Enterprise Control Room")

DB = "enterprise.db"
EXCEL_FILE = "DLF_Enterprise_Asset_Master_Template.xlsx"

# ---------------- DLF CORPORATE THEME ---------------- #
st.markdown("""
<style>
.stApp {background: linear-gradient(135deg,#071a2d,#0b2a45);}
h1,h2,h3,h4 {color:white;}
div[data-testid="metric-container"] {
   background-color: #0f3a5d;
   border-radius: 10px;
   padding: 15px;
   color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE INIT ---------------- #
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS assets(
        Asset_ID TEXT PRIMARY KEY,
        Asset_Name TEXT,
        Department TEXT,
        Location TEXT,
        Capacity TEXT,
        Make TEXT,
        Model TEXT,
        Installation_Date TEXT,
        Status TEXT,
        Criticality TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS energy(
        Date TEXT,
        Asset_ID TEXT,
        kWh REAL,
        BTU REAL,
        Diesel_Liters REAL,
        Cost_per_Unit REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS amc(
        Asset_ID TEXT,
        Vendor_Name TEXT,
        Contract_Type TEXT,
        Start_Date TEXT,
        Expiry_Date TEXT,
        Contract_Value REAL,
        Contact_Person TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS maintenance(
        Date TEXT,
        Asset_ID TEXT,
        Work_Type TEXT,
        Description TEXT,
        Downtime_Hours REAL,
        Action_Taken TEXT,
        Done_By TEXT,
        OEM_Involved TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

# ---------------- FIRST RUN EXCEL LOAD ---------------- #
def load_excel():
    conn = sqlite3.connect(DB)
    existing = pd.read_sql("SELECT * FROM assets", conn)

    if existing.empty and os.path.exists(EXCEL_FILE):
        xl = pd.ExcelFile(EXCEL_FILE)

        # Load Asset Master
        assets_df = xl.parse("ASSET_MASTER")
        assets_df.to_sql("assets", conn, if_exists="append", index=False)

        # Load Energy
        energy_df = xl.parse("ENERGY_LOG")
        energy_df.to_sql("energy", conn, if_exists="append", index=False)

        # Load AMC
        amc_df = xl.parse("AMC_TRACKING")
        amc_df.to_sql("amc", conn, if_exists="append", index=False)

        # Load Maintenance
        maint_df = xl.parse("MAINTENANCE_LOG")
        maint_df.to_sql("maintenance", conn, if_exists="append", index=False)

    conn.close()

load_excel()

# ---------------- LOGIN ---------------- #
def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

USERS = {"admin": hash_pass("Admin@123")}

if "login" not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    st.title("DLF Cyber Park – Enterprise Control Room")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u] == hash_pass(p):
            st.session_state.login = True
            st.success("Login Successful")
        else:
            st.error("Invalid Credentials")
    st.stop()

# ---------------- LOAD DB DATA ---------------- #
conn = sqlite3.connect(DB)
assets = pd.read_sql("SELECT * FROM assets", conn)
energy = pd.read_sql("SELECT * FROM energy", conn)
amc = pd.read_sql("SELECT * FROM amc", conn)
maintenance = pd.read_sql("SELECT * FROM maintenance", conn)

# ---------------- EXECUTIVE DASHBOARD ---------------- #
st.title("🏢 Executive Control Dashboard")

col1, col2, col3, col4 = st.columns(4)

total_assets = len(assets)
total_energy = energy["kWh"].sum() if not energy.empty else 0
total_btu = energy["BTU"].sum() if not energy.empty else 0
active_amc = len(amc)

col1.metric("Total Assets", total_assets)
col2.metric("Total Energy (kWh)", round(total_energy,2))
col3.metric("Total BTU", round(total_btu,2))
col4.metric("Active AMC Contracts", active_amc)

# ---------------- DEPARTMENT FILTER ---------------- #
dept_filter = st.selectbox("Select Department", assets["Department"].unique())
filtered_assets = assets[assets["Department"] == dept_filter]

st.subheader(f"{dept_filter} Assets")
st.dataframe(filtered_assets)

# ---------------- ENERGY SECTION ---------------- #
st.subheader("Energy Trend")
if not energy.empty:
    energy_group = energy.groupby("Date")["kWh"].sum()
    st.line_chart(energy_group)

# ---------------- AMC ALERT ---------------- #
st.subheader("AMC Expiry Alerts (Next 30 Days)")
if not amc.empty:
    amc["Expiry_Date"] = pd.to_datetime(amc["Expiry_Date"])
    alert = amc[amc["Expiry_Date"] < pd.Timestamp.today() + pd.Timedelta(days=30)]
    st.dataframe(alert)

# ---------------- MAINTENANCE SUMMARY ---------------- #
st.subheader("Maintenance Summary")
if not maintenance.empty:
    summary = maintenance.groupby("Work_Type").size()
    st.bar_chart(summary)

conn.close()
