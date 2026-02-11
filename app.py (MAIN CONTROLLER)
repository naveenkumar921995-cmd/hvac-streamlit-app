import streamlit as st
from database import create_tables
from auth import login_user
from kpi import calculate_kpi
from reports import generate_pdf
from alerts import check_amc_alerts

create_tables()

st.set_page_config(page_title="DLF Cyber Park - Executive Dashboard", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN ---------------- #
if not st.session_state.logged_in:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user(username, password):
            st.session_state.logged_in = True
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")

# ---------------- DASHBOARD ---------------- #
else:
    st.title("🏢 DLF Cyber Park – Executive Dashboard")

    kpi = calculate_kpi()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Assets", kpi["Total Assets"])
    col2.metric("Avg Health", kpi["Average Health"])
    col3.metric("Total Energy (kWh)", kpi["Total Energy"])
    col4.metric("KPI Score", kpi["KPI Score"])

    st.divider()

    st.subheader("⚠ AMC Alerts")
    alerts = check_amc_alerts()
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No AMC alerts")

    st.divider()

    if st.button("Generate Monthly PDF Report"):
        file = generate_pdf()
        with open(file, "rb") as f:
            st.download_button("Download Report", f, file_name=file)

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
