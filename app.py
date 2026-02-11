import streamlit as st
import pandas as pd
from datetime import datetime
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
st.set_page_config(page_title="DLF Cyber Park HVAC Control", layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- SAFE CSV LOADER ----------------
def load_csv(file, columns):
    path = f"{DATA_DIR}/{file}"
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        pd.DataFrame(columns=columns).to_csv(path, index=False)
    return pd.read_csv(path)

# ---------------- LOAD DATA ----------------
users = load_csv("users.csv", ["Employee_ID", "Name", "Role", "Password"])
assets = load_csv("assets.csv", ["Asset_ID","Asset_Name","Asset_Type","Location","Health","AMC_End_Date"])
logs = load_csv("daily_logs.csv", ["Date","Employee_ID","Asset_ID","Work_Type","Observation","Status"])
attendance = load_csv("attendance.csv", ["Date","Employee_ID"])
energy = load_csv("energy_meter.csv", ["Date","Asset_ID","kWh","BTU"])
amc = load_csv("amc_master.csv", ["Asset_ID","Vendor","AMC_Value","Start_Date","End_Date"])

# ---------------- LOGIN ----------------
st.sidebar.title("Login")
emp_id = st.sidebar.text_input("Employee ID").strip()
password = st.sidebar.text_input("Password", type="password").strip()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.sidebar.button("Login"):
    match = users[(users["Employee_ID"] == emp_id) & (users["Password"] == password)]
    if not match.empty:
        st.session_state.logged_in = True
        st.session_state.user = match.iloc[0]

        # Auto attendance
        today = datetime.now().strftime("%Y-%m-%d")
        if not ((attendance["Employee_ID"] == emp_id) & (attendance["Date"] == today)).any():
            new_att = pd.DataFrame([{"Date": today, "Employee_ID": emp_id}])
            attendance = pd.concat([attendance, new_att], ignore_index=True)
            attendance.to_csv(f"{DATA_DIR}/attendance.csv", index=False)
    else:
        st.sidebar.error("Invalid credentials")

if not st.session_state.logged_in:
    st.stop()

user = st.session_state.user
st.sidebar.success(f"{user['Name']} ({user['Role']})")

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menu", [
    "Live Wall Dashboard",
    "Energy & BTU",
    "AMC Management",
    "Daily Work Log",
    "Reports",
    "Attendance"
])

# ==========================================================
# 1️⃣ LIVE WALL DASHBOARD
# ==========================================================
if menu == "Live Wall Dashboard":
    st.title("Central HVAC Live Dashboard")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Assets", len(assets))
    col2.metric("Breakdowns", len(logs[logs["Work_Type"] == "Breakdown"]))
    col3.metric("Total Energy (kWh)", energy["kWh"].sum())

    st.subheader("Asset Health Overview")
    st.dataframe(assets)

# ==========================================================
# 2️⃣ ENERGY & BTU DASHBOARD
# ==========================================================
elif menu == "Energy & BTU":
    st.title("Energy & BTU Monitoring")

    with st.form("energy_form"):
        asset_id = st.selectbox("Asset", assets["Asset_ID"])
        kwh = st.number_input("kWh Reading", min_value=0.0)
        btu = st.number_input("BTU Reading", min_value=0.0)
        submit = st.form_submit_button("Submit")

    if submit:
        new_energy = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Asset_ID": asset_id,
            "kWh": kwh,
            "BTU": btu
        }])
        energy = pd.concat([energy, new_energy], ignore_index=True)
        energy.to_csv(f"{DATA_DIR}/energy_meter.csv", index=False)
        st.success("Energy data recorded")

    st.subheader("Energy Summary")
    total_kwh = energy["kWh"].sum()
    cost = total_kwh * 10  # ₹10 per unit assumption
    st.metric("Total Consumption (kWh)", total_kwh)
    st.metric("Estimated Energy Cost (₹)", cost)

# ==========================================================
# 3️⃣ AMC MANAGEMENT
# ==========================================================
elif menu == "AMC Management":
    st.title("AMC Vendor Management")

    with st.form("amc_form"):
        asset_id = st.selectbox("Asset", assets["Asset_ID"])
        vendor = st.text_input("Vendor Name")
        value = st.number_input("AMC Value (₹)", min_value=0.0)
        start = st.date_input("Start Date")
        end = st.date_input("End Date")
        submit = st.form_submit_button("Save AMC")

    if submit:
        new_amc = pd.DataFrame([{
            "Asset_ID": asset_id,
            "Vendor": vendor,
            "AMC_Value": value,
            "Start_Date": start,
            "End_Date": end
        }])
        amc = pd.concat([amc, new_amc], ignore_index=True)
        amc.to_csv(f"{DATA_DIR}/amc_master.csv", index=False)
        st.success("AMC saved")

    st.subheader("AMC Expiry Alerts")
    if not amc.empty:
        amc["End_Date"] = pd.to_datetime(amc["End_Date"], errors="coerce")
        expiring = amc[(amc["End_Date"] - pd.Timestamp.today()).dt.days <= 30]
        st.dataframe(expiring)

# ==========================================================
# 4️⃣ DAILY WORK LOG
# ==========================================================
elif menu == "Daily Work Log":
    st.title("Daily HVAC Work Log")

    with st.form("log_form"):
        asset_id = st.selectbox("Asset", assets["Asset_ID"])
        work_type = st.selectbox("Work Type", ["Routine","Preventive","Breakdown"])
        obs = st.text_area("Observation")
        status = st.selectbox("Health", ["OK","Attention"])
        submit = st.form_submit_button("Submit")

    if submit:
        new_log = pd.DataFrame([{
            "Date": datetime.now().strftime("%Y-%m-%d"),
            "Employee_ID": user["Employee_ID"],
            "Asset_ID": asset_id,
            "Work_Type": work_type,
            "Observation": obs,
            "Status": status
        }])
        logs = pd.concat([logs, new_log], ignore_index=True)
        logs.to_csv(f"{DATA_DIR}/daily_logs.csv", index=False)
        st.success("Log Saved")

# ==========================================================
# 5️⃣ REPORTS + PDF DOWNLOAD
# ==========================================================
elif menu == "Reports":
    st.title("Monthly Report")

    if not logs.empty:
        logs["Date"] = pd.to_datetime(logs["Date"], errors="coerce")
        month = st.selectbox("Select Month", logs["Date"].dt.month.unique())
        monthly = logs[logs["Date"].dt.month == month]

        summary = monthly.groupby(["Asset_ID","Work_Type"]).size().reset_index(name="Count")
        st.dataframe(summary)

        if st.button("Generate PDF Report"):
            file_path = "hvac_monthly_report.pdf"
            doc = SimpleDocTemplate(file_path)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph("DLF Cyber Park HVAC Monthly Report", styles["Heading1"]))
            elements.append(Spacer(1, 0.5 * inch))
            elements.append(Paragraph(str(summary.to_string()), styles["Normal"]))
            doc.build(elements)

            with open(file_path, "rb") as f:
                st.download_button("Download PDF", f, file_name="HVAC_Report.pdf")

# ==========================================================
# 6️⃣ ATTENDANCE
# ==========================================================
elif menu == "Attendance":
    st.title("Attendance Record")
    st.dataframe(attendance)
