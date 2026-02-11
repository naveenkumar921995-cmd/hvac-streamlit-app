import streamlit as st
import pandas as pd
import sqlite3
import os
import bcrypt
from datetime import datetime, date
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="DLF Cyber Park IFM", layout="wide")

# ------------------------------------------------------------
# PREMIUM DLF CORPORATE THEME
# ------------------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
}
.stApp {
    background: linear-gradient(135deg, #0b1e36 0%, #142c4f 100%);
    color: white;
}
h1, h2, h3 {
    color: #d4af37;
    font-weight: 600;
}
div[data-testid="metric-container"] {
    background: #1c355e;
    border: 1px solid #d4af37;
    padding: 18px;
    border-radius: 14px;
}
.sidebar .sidebar-content {
    background-color: #162b4a;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# DATABASE SETUP
# ------------------------------------------------------------
DB = "cyberpark_enterprise.db"
conn = sqlite3.connect(DB, check_same_thread=False)
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
role TEXT
)
""")

# ASSETS
cursor.execute("""
CREATE TABLE IF NOT EXISTS assets(
id INTEGER PRIMARY KEY AUTOINCREMENT,
asset_name TEXT,
department TEXT,
health TEXT DEFAULT 'OK',
amc_end DATE,
compliance_end DATE
)
""")

# ENERGY
cursor.execute("""
CREATE TABLE IF NOT EXISTS energy_logs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
asset_name TEXT,
log_date DATE,
kwh REAL,
btu REAL,
cost REAL
)
""")

# ATTENDANCE
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
login_time TEXT
)
""")

conn.commit()

# ------------------------------------------------------------
# DEFAULT ADMIN
# ------------------------------------------------------------
def create_admin():
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)",
                       ("admin", hashed, "Admin"))
        conn.commit()

create_admin()

# ------------------------------------------------------------
# SMART DEPARTMENT CLASSIFICATION
# ------------------------------------------------------------
def detect_department(name):
    name = name.lower()
    if any(x in name for x in ["ahu","chiller","hvac"]):
        return "HVAC"
    if any(x in name for x in ["dg","generator"]):
        return "DG"
    if "stp" in name: return "STP"
    if "wtp" in name: return "WTP"
    if "lift" in name: return "Lifts"
    if "fire" in name: return "Fire Fighting"
    if "cctv" in name: return "CCTV"
    if "bms" in name: return "BMS"
    if any(x in name for x in ["panel","electrical"]):
        return "Electrical"
    if "vent" in name: return "Ventilation"
    if "facade" in name: return "Facade"
    return "General"

# ------------------------------------------------------------
# IMPORT ASSET FILE (AUTO)
# ------------------------------------------------------------
def import_assets():
    cursor.execute("SELECT COUNT(*) FROM assets")
    if cursor.fetchone()[0] == 0:
        if os.path.exists("Asset_cyberpark.xlsx"):
            df = pd.read_excel("Asset_cyberpark.xlsx")
            df = df.dropna(axis=1, how='all')

            name_col = None
            for col in df.columns:
                if any(x in col.lower() for x in ["equipment","asset","name"]):
                    name_col = col
                    break

            if name_col is None:
                name_col = df.columns[1]

            for asset in df[name_col].dropna():
                dept = detect_department(str(asset))
                cursor.execute(
                    "INSERT INTO assets(asset_name,department) VALUES (?,?)",
                    (str(asset), dept)
                )
            conn.commit()

import_assets()

# ------------------------------------------------------------
# LOGIN SYSTEM
# ------------------------------------------------------------
st.sidebar.title("DLF Cyber Park Login")

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if user and bcrypt.checkpw(password.encode(), user[0]):
        st.session_state["user"] = username
        st.session_state["role"] = user[1]
        cursor.execute("INSERT INTO attendance(username,login_time) VALUES (?,?)",
                       (username,str(datetime.now())))
        conn.commit()
    else:
        st.sidebar.error("Invalid Credentials")

if "user" not in st.session_state:
    st.stop()

st.sidebar.success(f"{st.session_state['user']} ({st.session_state['role']})")

menu = st.sidebar.radio("Navigation",[
    "Executive Dashboard",
    "Enterprise Live Wall",
    "Energy & BTU Analytics",
    "AMC & Compliance",
    "Attendance",
    "Monthly PDF Report"
])

# ------------------------------------------------------------
# EXECUTIVE DASHBOARD
# ------------------------------------------------------------
if menu == "Executive Dashboard":

    st.title("Executive Command Center")

    assets_df = pd.read_sql("SELECT * FROM assets", conn)
    energy_df = pd.read_sql("SELECT * FROM energy_logs", conn)

    total_assets = len(assets_df)
    departments = assets_df["department"].nunique()
    attention = len(assets_df[assets_df["health"]!="OK"])
    total_energy = energy_df["kwh"].sum() if not energy_df.empty else 0
    total_cost = energy_df["cost"].sum() if not energy_df.empty else 0

    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("Total Assets", total_assets)
    col2.metric("Departments", departments)
    col3.metric("Attention Required", attention)
    col4.metric("Energy (kWh)", round(total_energy,2))
    col5.metric("Energy Cost ₹", round(total_cost,2))

    fig = px.pie(assets_df, names="department",
                 color_discrete_sequence=px.colors.sequential.Agsunset)
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# LIVE WALL
# ------------------------------------------------------------
elif menu == "Enterprise Live Wall":
    st.title("All Departments – Live Asset Wall")
    df = pd.read_sql("SELECT asset_name,department,health FROM assets", conn)
    st.dataframe(df, use_container_width=True)

# ------------------------------------------------------------
# ENERGY & BTU
# ------------------------------------------------------------
elif menu == "Energy & BTU Analytics":

    st.title("Energy & BTU Monitoring")

    assets_list = pd.read_sql("SELECT asset_name FROM assets", conn)["asset_name"].tolist()

    with st.form("energy"):
        asset = st.selectbox("Asset", assets_list)
        kwh = st.number_input("kWh")
        btu = st.number_input("BTU")
        cost = st.number_input("Cost ₹")
        submit = st.form_submit_button("Submit")

    if submit:
        cursor.execute("""
        INSERT INTO energy_logs(asset_name,log_date,kwh,btu,cost)
        VALUES(?,?,?,?,?)
        """,(asset,str(date.today()),kwh,btu,cost))
        conn.commit()
        st.success("Energy Data Saved")

    df = pd.read_sql("SELECT * FROM energy_logs", conn)
    if not df.empty:
        fig = px.bar(df,x="asset_name",y="kwh",
                     color="kwh",
                     color_continuous_scale="Agsunset")
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# AMC & COMPLIANCE
# ------------------------------------------------------------
elif menu == "AMC & Compliance":

    st.title("AMC & Compliance Tracking")

    df = pd.read_sql("SELECT * FROM assets", conn)

    asset = st.selectbox("Asset", df["asset_name"])
    amc = st.date_input("AMC End Date")
    comp = st.date_input("Compliance End Date")

    if st.button("Update"):
        cursor.execute("""
        UPDATE assets SET amc_end=?, compliance_end=? WHERE asset_name=?
        """,(str(amc),str(comp),asset))
        conn.commit()
        st.success("Updated")

    today = str(date.today())
    expiring = df[
        (df["amc_end"] < today) |
        (df["compliance_end"] < today)
    ]
    st.subheader("Expired / Expiring Assets")
    st.dataframe(expiring)

# ------------------------------------------------------------
# ATTENDANCE
# ------------------------------------------------------------
elif menu == "Attendance":
    st.title("Attendance Log")
    df = pd.read_sql("SELECT * FROM attendance", conn)
    st.dataframe(df)

# ------------------------------------------------------------
# PDF REPORT
# ------------------------------------------------------------
elif menu == "Monthly PDF Report":

    st.title("Generate Enterprise Monthly Report")

    if st.button("Generate PDF"):

        doc = SimpleDocTemplate("DLF_Monthly_Report.pdf")
        styles = getSampleStyleSheet()
        elements = []

        assets_df = pd.read_sql("SELECT * FROM assets", conn)
        energy_df = pd.read_sql("SELECT * FROM energy_logs", conn)

        elements.append(Paragraph("DLF Cyber Park - Monthly IFM Report", styles["Title"]))
        elements.append(Spacer(1,20))
        elements.append(Paragraph(f"Total Assets: {len(assets_df)}", styles["Normal"]))
        elements.append(Paragraph(f"Total Energy kWh: {energy_df['kwh'].sum()}", styles["Normal"]))
        elements.append(Paragraph(f"Total Energy Cost: ₹ {energy_df['cost'].sum()}", styles["Normal"]))

        doc.build(elements)

        with open("DLF_Monthly_Report.pdf","rb") as f:
            st.download_button("Download Report",f,"DLF_Monthly_Report.pdf")
