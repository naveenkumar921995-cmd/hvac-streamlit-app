import os
import pandas as pd
import streamlit as st

# Ensure data directory exists (FIX FOR STREAMLIT CLOUD)
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# ---------------- CONFIG ----------------
st.set_page_config("DLF Cyber Park – HVAC", layout="wide")
DATA = "data/"

# ---------------- SAFE FILE LOADER ----------------
def load_csv(filename, columns):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        pd.DataFrame(columns=columns).to_csv(path, index=False)
    return pd.read_csv(path)
    except:
        return pd.DataFrame(columns=columns)

# ---------------- LOAD DATA ----------------
assets = load_csv("assets.csv", [
    "Asset_ID","Asset_Name","Asset_Type","Location",
    "Health","AMC_End_Date","OEM_Warranty_End","Compliance_End_Date"
])

users = load_csv("users.csv", [
    "Employee_ID","Employee_Name","Role","Password"
])

logs = load_csv("daily_logs.csv", [
    "Date","Employee_ID","Asset_ID","Work_Type","Observation","Status"
])

alerts = load_csv("alerts.csv", [
    "Date","Asset_ID","Alert_Type","Severity","Assigned_To","Message"
])

# ---------------- LOGIN ----------------
st.sidebar.title("Login")

emp_id = st.sidebar.text_input("Employee ID")
password = st.sidebar.text_input("Password", type="password")

if emp_id == "" or password == "":
    st.stop()

user = users[
    (users["Employee_ID"] == emp_id) &
    (users["Password"] == password)
]

if user.empty:
    st.sidebar.error("Invalid credentials")
    st.stop()

user = user.iloc[0]
st.sidebar.success(f"{user['Employee_Name']} ({user['Role']})")

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Daily Work Log",
    "Alerts",
    "Assets"
])

# ---------------- HELPER: DATE CHECK ----------------
def expiry_status(end_date):
    if pd.isna(end_date) or end_date == "":
        return None
    days = (pd.to_datetime(end_date).date() - date.today()).days
    if days < 0:
        return "Expired"
    if days <= 7:
        return "Urgent"
    if days <= 30:
        return "Warning"
    return "OK"

# ---------------- PHASE 3 & 4 ALERT ENGINE ----------------
new_alerts = []

for _, a in assets.iterrows():

    # Health alerts
    if a["Health"] == "Critical":
        new_alerts.append([
            date.today(), a["Asset_ID"], "Health",
            "Critical", "Admin",
            f"{a['Asset_Name']} marked Critical"
        ])

    # AMC / OEM / Compliance
    for col, label in [
        ("AMC_End_Date","AMC"),
        ("OEM_Warranty_End","OEM"),
        ("Compliance_End_Date","Compliance")
    ]:
        status = expiry_status(a[col])
        if status in ["Warning","Urgent","Expired"]:
            new_alerts.append([
                date.today(), a["Asset_ID"], label,
                status, "Purchase",
                f"{label} {status} for {a['Asset_Name']}"
            ])

if new_alerts:
    alerts = pd.concat([alerts, pd.DataFrame(new_alerts, columns=alerts.columns)])
    alerts.drop_duplicates(inplace=True)
    alerts.to_csv(DATA+"alerts.csv", index=False)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("HVAC Dashboard")

    c1,c2,c3 = st.columns(3)
    c1.metric("Total Assets", len(assets))
    c2.metric("Critical Alerts", len(alerts[alerts["Severity"]=="Critical"]))
    c3.metric("Expired AMC / Compliance", len(alerts[alerts["Severity"]=="Expired"]))

    st.subheader("Recent Alerts")
    st.dataframe(alerts.tail(10))

# ---------------- DAILY WORK LOG ----------------
elif menu == "Daily Work Log":
    st.title("Daily HVAC Work Update")

    with st.form("log"):
        asset = st.selectbox("Asset", assets["Asset_ID"])
        work = st.selectbox("Work Type", ["Routine","Preventive","Breakdown"])
        obs = st.text_area("Observation")
        status = st.selectbox("Asset Health", ["OK","Attention","Critical"])
        submit = st.form_submit_button("Submit")

    if submit:
        logs = pd.concat([logs, pd.DataFrame([{
            "Date": date.today(),
            "Employee_ID": emp_id,
            "Asset_ID": asset,
            "Work_Type": work,
            "Observation": obs,
            "Status": status
        }])])

        assets.loc[assets["Asset_ID"]==asset, "Health"] = status

        logs.to_csv(DATA+"daily_logs.csv", index=False)
        assets.to_csv(DATA+"assets.csv", index=False)

        st.success("Work log saved")

# ---------------- ALERTS VIEW ----------------
elif menu == "Alerts":
    st.title("System Alerts")

    if user["Role"] == "Purchase":
        st.dataframe(alerts[alerts["Assigned_To"]=="Purchase"])
    else:
        st.dataframe(alerts)

# ---------------- ASSETS ----------------
elif menu == "Assets":
    st.title("Asset Master")
    st.dataframe(assets)

