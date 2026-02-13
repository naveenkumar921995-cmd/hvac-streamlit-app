import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="DLF CyberPark",
    layout="wide"
)

# ===============================
# DARK DLF CORPORATE THEME
# ===============================
st.markdown("""
<style>
.stApp {background-color: #0A192F; color: #E6F1FF;}
h1,h2,h3 {color: #00F0FF;}
div[data-testid="stMetric"] {
    background-color:#112240;
    padding:20px;
    border-radius:15px;
}
.sidebar .sidebar-content {
    background-color:#0F3057;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# HEADER WITH LOGOS
# ===============================
col1, col2, col3 = st.columns([1,6,1])

with col1:
    if os.path.exists("dlf_logo.png"):
        st.image("dlf_logo.png", width=120)

with col2:
    st.markdown(
        "<h1 style='text-align:center;'>DLF ENTERPRISE CONTROL ROOM V6</h1>",
        unsafe_allow_html=True
    )

with col3:
    if os.path.exists("lnp_logo.png"):
        st.image("lnp_logo.png", width=120)

st.markdown("---")

# ===============================
# DATABASE SETUP
# ===============================
DB_FILE = "enterprise_v6.db"
EXCEL_FILE = "DLF_Enterprise_Asset_Master_Template.xlsx"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Asset_ID TEXT,
        Asset_Name TEXT,
        Department TEXT,
        Location TEXT,
        Capacity TEXT,
        Make TEXT,
        Model TEXT,
        Installation_Date TEXT,
        Status TEXT,
        Criticality TEXT
    )
    """)
    conn.commit()
    conn.close()

def auto_load_excel():
    conn = sqlite3.connect(DB_FILE)
    existing = pd.read_sql("SELECT * FROM assets", conn)

    if len(existing) == 0:
        if os.path.exists(EXCEL_FILE):
            df = pd.read_excel(EXCEL_FILE, engine="openpyxl")
            df.columns = df.columns.str.strip()

            required_cols = [
                "Asset_ID",
                "Asset_Name",
                "Department",
                "Location",
                "Capacity",
                "Make",
                "Model",
                "Installation_Date",
                "Status",
                "Criticality"
            ]

            missing = [col for col in required_cols if col not in df.columns]

            if len(missing) == 0:
                df = df[required_cols]
                df.to_sql("assets", conn, if_exists="replace", index=False)
            else:
                st.error(f"Missing Columns in Excel: {missing}")

    conn.close()

init_db()
auto_load_excel()

# ===============================
# LOAD DATA
# ===============================
conn = sqlite3.connect(DB_FILE)
df = pd.read_sql("SELECT * FROM assets", conn)
conn.close()

# ===============================
# SIDEBAR
# ===============================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "",
    ["Boardroom Dashboard", "Asset Intelligence", "Control Room Mode"]
)

# ===============================
# KPI CALCULATION
# ===============================
total_assets = len(df)
active_assets = len(df[df["Status"] == "Active"]) if not df.empty else 0
critical_assets = len(df[df["Criticality"] == "High"]) if not df.empty else 0

# ===============================
# BOARDROOM DASHBOARD
# ===============================
if page == "Boardroom Dashboard":

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Assets", total_assets)
    col2.metric("Active Assets", active_assets)
    col3.metric("Critical Assets", critical_assets)

    st.markdown("### Department Distribution")
    if not df.empty:
        st.bar_chart(df["Department"].value_counts())

# ===============================
# ASSET INTELLIGENCE
# ===============================
elif page == "Asset Intelligence":

    st.subheader("Asset Register")

    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No assets loaded.")

# ===============================
# CONTROL ROOM MODE
# ===============================
elif page == "Control Room Mode":

    st.subheader("Live Control Wall")

    if not df.empty:
        critical = df[df["Criticality"] == "High"]
        st.write("High Critical Assets")
        st.dataframe(critical, use_container_width=True)
    else:
        st.warning("No live data available.")

# ===============================
# FOOTER
# ===============================
st.markdown("---")
st.caption(f"System Time: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
