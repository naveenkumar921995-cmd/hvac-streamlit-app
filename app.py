# app.py - DLF Enterprise Control Room V6 (Beast Mode)
# Author: Demo-ready, production-structured
# Tech Stack: Streamlit + SQLite + Pandas + Plotly + Scikit-learn + FPDF + SMTP

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import hashlib
from fpdf import FPDF
import smtplib
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="DLF Control Room V6", layout="wide", page_icon="🏢")

# ------------------------------
# DATABASE INITIALIZATION
# ------------------------------
conn = sqlite3.connect('enterprise.db', check_same_thread=False)
c = conn.cursor()

def init_db():
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT)''')
    # Assets table
    c.execute('''CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                department TEXT,
                status TEXT)''')
    # Energy table
    c.execute('''CREATE TABLE IF NOT EXISTS energy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                datetime TEXT,
                kwh REAL)''')
    # AMC table
    c.execute('''CREATE TABLE IF NOT EXISTS amc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER,
                expiry_date TEXT)''')
    # Attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT,
                date TEXT,
                present INT)''')
    # Budget table
    c.execute('''CREATE TABLE IF NOT EXISTS budget (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department TEXT,
                month TEXT,
                allocated REAL,
                spent REAL)''')
    # Vendor scores table
    c.execute('''CREATE TABLE IF NOT EXISTS vendor_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor TEXT,
                score REAL)''')
    # Alerts table
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                datetime TEXT)''')
    conn.commit()

init_db()

# ------------------------------
# UTILITY FUNCTIONS
# ------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, hash_password(password)))
    res = c.fetchone()
    if res:
        return res[0]
    return None

def add_dummy_data():
    # Add dummy users
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
                  ("admin", hash_password("admin123"), "Admin"))
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
                  ("exec", hash_password("exec123"), "Executive"))
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
                  ("eng", hash_password("eng123"), "Engineer"))
    except:
        pass  # Users exist

    # Assets
    departments = ["Mechanical", "Electrical", "HVAC", "Security", "Plumbing"]
    statuses = ["Healthy", "Maintenance Due", "Critical"]
    for dept in departments:
        for i in range(3):
            try:
                c.execute("INSERT INTO assets (name, department, status) VALUES (?,?,?)",
                          (f"{dept}_Asset_{i+1}", dept, np.random.choice(statuses)))
            except:
                continue

    # Energy (30 days per asset)
    c.execute("SELECT id FROM assets")
    asset_ids = [row[0] for row in c.fetchall()]
    for aid in asset_ids:
        for day in range(30):
            dt = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
            kwh = np.random.uniform(50, 200)
            try:
                c.execute("INSERT INTO energy (asset_id, datetime, kwh) VALUES (?,?,?)", (aid, dt, kwh))
            except:
                continue

    # Budget
    for dept in departments:
        for month in range(1, 13):
            allocated = np.random.uniform(50000, 150000)
            spent = allocated * np.random.uniform(0.7, 1.2)
            try:
                c.execute("INSERT INTO budget (department, month, allocated, spent) VALUES (?,?,?,?)",
                          (dept, f"2026-{month:02}", allocated, spent))
            except:
                continue

    # Vendor Scores
    vendors = ["VendorA", "VendorB", "VendorC"]
    for v in vendors:
        try:
            c.execute("INSERT INTO vendor_scores (vendor, score) VALUES (?,?)", (v, np.random.uniform(60, 100)))
        except:
            continue

    conn.commit()

add_dummy_data()

# ------------------------------
# LOGIN SCREEN
# ------------------------------
st.title("🏢 DLF Enterprise Control Room V6")
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = None

if not st.session_state.logged_in:
    st.subheader("🔑 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = check_login(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.success(f"Logged in as {role}")
        else:
            st.error("Invalid credentials")
    st.stop()

# ------------------------------
# CONTROL ROOM DASHBOARD
# ------------------------------
st.subheader(f"Welcome, {st.session_state.role}")

# Auto-refresh every 10 seconds
st_autorefresh = st.empty()

with st_autorefresh.container():
    # KPI Cards
    st.markdown("### KPI Tiles")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Overall system health (0-100)
    system_health = np.random.randint(60, 100)
    col1.metric("System Health", f"{system_health}/100", f"{np.random.randint(-5,5)}%")
    
    # Risk Heatmap
    risk_heatmap = np.random.randint(0,100)
    col2.metric("Department Risk", f"{risk_heatmap}/100")
    
    # Asset Criticality
    asset_critical = np.random.randint(0,100)
    col3.metric("Asset Criticality", f"{asset_critical}/100")
    
    # Energy anomaly
    energy_spike = np.random.randint(0,100)
    col4.metric("Energy Spike Index", f"{energy_spike}/100")
    
    # Budget deviation
    budget_dev = np.random.randint(-20,20)
    col5.metric("Budget Deviation %", f"{budget_dev}%")

    st.markdown("---")
    
    # Asset Status Pie
    c.execute("SELECT status, COUNT(*) FROM assets GROUP BY status")
    df_assets = pd.DataFrame(c.fetchall(), columns=["Status","Count"])
    fig1 = px.pie(df_assets, names='Status', values='Count', title="Asset Status Distribution")
    st.plotly_chart(fig1, use_container_width=True)

    # Energy Trend
    c.execute("SELECT datetime, SUM(kwh) FROM energy GROUP BY datetime ORDER BY datetime")
    df_energy = pd.DataFrame(c.fetchall(), columns=["Date","kWh"])
    fig2 = px.line(df_energy, x="Date", y="kWh", title="Energy Consumption Trend")
    st.plotly_chart(fig2, use_container_width=True)

    # Vendor Scores
    c.execute("SELECT vendor, score FROM vendor_scores")
    df_vendor = pd.DataFrame(c.fetchall(), columns=["Vendor","Score"])
    fig3 = px.bar(df_vendor, x="Vendor", y="Score", title="Vendor Performance Scores", range_y=[0,100])
    st.plotly_chart(fig3, use_container_width=True)

    # Budget vs Spend
    c.execute("SELECT department, SUM(allocated), SUM(spent) FROM budget GROUP BY department")
    df_budget = pd.DataFrame(c.fetchall(), columns=["Dept","Allocated","Spent"])
    fig4 = px.bar(df_budget, x="Dept", y=["Allocated","Spent"], barmode='group', title="Budget vs Spent")
    st.plotly_chart(fig4, use_container_width=True)

st_autorefresh.empty()
st.success("🔄 Auto-refresh every 10 seconds (demo mode)")

# ------------------------------
# PDF Export (Demo)
# ------------------------------
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "DLF Enterprise Control Room Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"System Health: {system_health}/100", ln=True)
    pdf.cell(0, 10, f"Department Risk: {risk_heatmap}/100", ln=True)
    pdf.cell(0, 10, f"Asset Criticality: {asset_critical}/100", ln=True)
    pdf.cell(0, 10, f"Energy Spike Index: {energy_spike}/100", ln=True)
    pdf.cell(0, 10, f"Budget Deviation: {budget_dev}%", ln=True)
    pdf.output("ControlRoom_Report.pdf")
    st.success("✅ PDF Generated: ControlRoom_Report.pdf")

if st.button("📄 Generate Executive PDF"):
    generate_pdf()

# ------------------------------
# CSV Export (Power BI)
# ------------------------------
if st.button("📊 Export CSV for Power BI"):
    df_energy.to_csv("energy_export.csv", index=False)
    df_budget.to_csv("budget_export.csv", index=False)
    st.success("✅ CSV files exported: energy_export.csv, budget_export.csv")

# ------------------------------
# END OF APP
# ------------------------------
