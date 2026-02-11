import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import init_db, get_connection
from auth import create_admin
from theme import load_theme
from utils import classify_asset

# INIT SYSTEM
init_db()
create_admin()
load_theme()

st.title("🏢 DLF CYBER PARK – ENTERPRISE CONTROL ROOM V3")

# LOGIN
if "user" not in st.session_state:
    st.session_state.user = None

username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()

    if user:
        import bcrypt
        if bcrypt.checkpw(password.encode(), user[2]):
            st.session_state.user = username
            st.success("Login Successful")
        else:
            st.error("Wrong Password")
    else:
        st.error("User Not Found")

# DASHBOARD
if st.session_state.user:

    conn = get_connection()

    df_assets = pd.read_sql("SELECT * FROM assets", conn)
    df_energy = pd.read_sql("SELECT * FROM energy", conn)
    df_amc = pd.read_sql("SELECT * FROM amc", conn)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Assets", len(df_assets))
    col2.metric("Total Energy (kWh)", df_energy["kwh"].sum() if not df_energy.empty else 0)
    col3.metric("Total BTU", df_energy["btu"].sum() if not df_energy.empty else 0)
    col4.metric("Active AMC", len(df_amc))

    st.subheader("Department Distribution")

    if not df_assets.empty:
        fig = px.pie(df_assets, names="department")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Live Control Wall")

    departments = df_assets["department"].unique() if not df_assets.empty else []

    for dept in departments:
        count = len(df_assets[df_assets["department"] == dept])
        st.markdown(f"""
        <div style='background:#132f4c;padding:20px;border-radius:10px;margin-bottom:10px'>
        <h3>{dept} - {count} Assets</h3>
        </div>
        """, unsafe_allow_html=True)

    # PDF REPORT
    if st.button("Generate Monthly Report"):
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet

        doc = SimpleDocTemplate("monthly_report.pdf")
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("DLF Cyber Park - Monthly Report", styles["Title"]))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Total Assets: {len(df_assets)}", styles["Normal"]))

        doc.build(elements)

        with open("monthly_report.pdf", "rb") as f:
            st.download_button("Download Report", f, "Monthly_Report.pdf")

    conn.close()
