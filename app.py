import streamlit as st
import pandas as pd
from datetime import datetime
import os

# ---------------- CONFIG ----------------
st.set_page_config(page_title="HVAC Asset Management – DLF Cyber Park", layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- SAFE CSV LOADER ----------------
def load_csv(file, columns):
    path = f"{DATA_DIR}/{file}"
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(path, index=False)
    return pd.read_csv(path)

# ---------------- LOAD DATA (IMPORTANT: MUST COME BEFORE LOGIN) ----------------
users = load_csv("users.csv", ["Employee_ID", "Name", "Role", "Password"])
assets = load_csv("assets.csv", [
    "Asset_ID", "Asset_Name", "Asset_Type",
    "Location", "Health", "AMC_End_Date"
])
logs = load_csv("daily_logs.csv", [
    "Date", "Employee_ID", "Asset_ID",
    "Work_Type", "Observation", "Status"
])
attendance = load_csv("attendance.csv", ["Date", "Employee_ID"])

# ---------------- LOGIN ----------------
st.sidebar.title("Login")

emp_id = st.sidebar.text_input("Employee ID").strip()
password = st.sidebar.text_input("Password", type="password").strip()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.sidebar.button("Login"):
    match = users[
        (users["Employee_ID"] == emp_id) &
        (users["Password"] == password)
    ]

    if not match.empty:
        st.session_state.logged_in = True
        st.session_state.user = match.iloc[0]

        # Auto Attendance
        today = datetime.now().strftime("%Y-%m-%d")
        if not ((attendance["Employee_ID"] == emp_id) &
                (attendance["Date"] == today)).any():
            new_att = pd.DataFrame([{
                "Date": today,
                "Employee_ID": emp_id
            }])
            attendance = pd.concat([attendance, new_att], ignore_index=True)
            attendance.to_csv(f"{DATA_DIR}/attendance.csv", index=False)

    else:
        st.sidebar.error("Invalid credentials")

if not st.session_state.logged_in:
    st.stop()

user = st.session_state.user
st.sidebar.success(f"{user['Name']} ({user['Role']})")

# ---------------- ROLE BASED MENU ----------------
if user["Role"] == "Admin":
    menu = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Daily Work Log", "Assets", "Reports", "Attendance"]
    )
else:
    menu = st.sidebar.radio(
        "Menu",
        ["Dashboard", "Daily Work Log", "Assets"]
    )

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("HVAC Asset Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", len(assets))
    col2.metric("OK", len(assets[assets["Health"] == "OK"]))
    col3.metric("Attention", len(assets[assets["Health"] == "Attention"]))

    st.subheader("AMC Expiry Alerts")

    if not assets.empty:
        assets["AMC_End_Date"] = pd.to_datetime(
            assets["AMC_End_Date"], errors="coerce"
        )
        today = pd.Timestamp.today()

        expiring = assets[
            (assets["AMC_End_Date"] - today).dt.days <= 30
        ]

        if not expiring.empty:
            st.warning("AMC expiring within 30 days")
            st.dataframe(expiring)
        else:
            st.success("All AMC contracts valid")

# ---------------- DAILY WORK LOG ----------------
elif menu == "Daily Work Log":
    st.title("Daily HVAC Work Log")

    with st.form("log_form"):
        asset_id = st.selectbox("Asset", assets["Asset_ID"])
        work_type = st.selectbox("Work Type", ["Routine", "Preventive", "Breakdown"])
        observation = st.text_area("Observation")
        status = st.selectbox("Asset Health", ["OK", "Attention"])
        submit = st.form_submit_button("Submit")

    if submit:
        new_log = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Employee_ID": user["Employee_ID"],
            "Asset_ID": asset_id,
            "Work_Type": work_type,
            "Observation": observation,
            "Status": status
        }])

        logs = pd.concat([logs, new_log], ignore_index=True)
        logs.to_csv(f"{DATA_DIR}/daily_logs.csv", index=False)

        assets.loc[assets["Asset_ID"] == asset_id, "Health"] = status
        assets.to_csv(f"{DATA_DIR}/assets.csv", index=False)

        st.success("Work log submitted successfully")

# ---------------- REPORTS ----------------
elif menu == "Reports":
    st.title("Monthly Report")

    if not logs.empty:
        logs["Date"] = pd.to_datetime(logs["Date"], errors="coerce")
        month = st.selectbox("Select Month", logs["Date"].dt.month.unique())

        monthly = logs[logs["Date"].dt.month == month]

        summary = monthly.groupby(
            ["Asset_ID", "Work_Type"]
        ).size().reset_index(name="Count")

        st.dataframe(summary)

    else:
        st.info("No logs available")

# ---------------- ATTENDANCE ----------------
elif menu == "Attendance":
    st.title("Attendance Record")
    st.dataframe(attendance)
