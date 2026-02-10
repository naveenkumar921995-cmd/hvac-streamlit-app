import os
import pandas as pd
import streamlit as st
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="HVAC Asset Management", layout="wide")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- SAFE CSV LOADER ----------------
def load_csv(filename, columns):
    path = os.path.join(DATA_DIR, filename)
    try:
        if not os.path.exists(path):
            df = pd.DataFrame(columns=columns)
            df.to_csv(path, index=False)
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return pd.DataFrame(columns=columns)

# ---------------- LOAD DATA ----------------
users = load_csv(
    "users.csv",
    ["Employee_ID", "Name", "Role", "Password"]
)

assets = load_csv(
    "assets.csv",
    [
        "Asset_ID",
        "Asset_Name",
        "Asset_Type",
        "Location",
        "Health",
        "AMC_End_Date",
        "OEM_Warranty_End",
        "Compliance_End_Date"
    ]
)

# ---------------- LOGIN ----------------
st.sidebar.title("🔐 Login")

if users.empty:
    st.warning("No users found. Please add users.csv in data folder.")
    st.stop()

user_id = st.sidebar.selectbox("Employee ID", users["Employee_ID"])
password = st.sidebar.text_input("Password", type="password")

login_btn = st.sidebar.button("Login")

if not login_btn:
    st.stop()

user = users[users["Employee_ID"] == user_id]

if user.empty or password != str(user.iloc[0]["Password"]):
    st.sidebar.error("Invalid credentials")
    st.stop()

st.sidebar.success(f"Welcome {user.iloc[0]['Name']} ({user.iloc[0]['Role']})")

# ---------------- DASHBOARD (PHASE 3) ----------------
st.title("🏢 HVAC Asset Management Dashboard")

col1, col2, col3 = st.columns(3)

col1.metric("Total Assets", len(assets))

if "Health" in assets.columns:
    col2.metric(
        "Attention Required",
        len(assets[assets["Health"] == "Attention"])
    )
else:
    col2.metric("Attention Required", 0)

# ---------------- EXPIRY LOGIC (PHASE 4) ----------------
def days_left(date_str):
    try:
        return (pd.to_datetime(date_str) - datetime.today()).days
    except:
        return None

expiry_alerts = []

for _, row in assets.iterrows():
    for col in ["AMC_End_Date", "OEM_Warranty_End", "Compliance_End_Date"]:
        days = days_left(row[col])
        if days is not None and days <= 30:
            expiry_alerts.append({
                "Asset_ID": row["Asset_ID"],
                "Asset_Name": row["Asset_Name"],
                "Type": col.replace("_", " "),
                "Days Left": days
            })

expiry_df = pd.DataFrame(expiry_alerts)

col3.metric("Expiring ≤ 30 days", len(expiry_df))

# ---------------- TABLES ----------------
st.subheader("📋 Asset List")
st.dataframe(assets, use_container_width=True)

if not expiry_df.empty:
    st.subheader("⏰ Expiry Alerts (Next 30 Days)")
    st.dataframe(expiry_df, use_container_width=True)
else:
    st.success("No upcoming expiries 🎉")

# ---------------- FOOTER ----------------
st.caption("HVAC Asset Manager | Streamlit Cloud Ready ✅")
