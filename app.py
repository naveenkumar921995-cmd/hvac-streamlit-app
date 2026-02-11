import streamlit as st
import pandas as pd
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ---------------- CONFIG ---------------- #
st.set_page_config(page_title="DLF HVAC Command Center", layout="wide")
DATA_PATH = "data"
os.makedirs(DATA_PATH, exist_ok=True)

# ---------------- SAFE CSV LOADER ---------------- #
def load_csv(filename, columns):
    path = os.path.join(DATA_PATH, filename)

    if not os.path.exists(path):
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

    try:
        df = pd.read_csv(path)
    except:
        df = pd.DataFrame(columns=columns)

    df.columns = df.columns.str.strip()

    for col in columns:
        if col not in df.columns:
            df[col] = ""

    return df

# ---------------- LOAD DATA ---------------- #
users = load_csv("users.csv", ["Employee_ID", "Name", "Password", "Role"])
assets = load_csv("assets.csv", [
    "Asset_ID","Asset_Name","Asset_Type","Location",
    "Health","AMC_Vendor","AMC_End_Date"
])
energy = load_csv("energy.csv", [
    "Date","Asset_ID","kWh","BTU","Cost_per_kWh"
])

# Convert numeric safely
energy["kWh"] = pd.to_numeric(energy["kWh"], errors="coerce").fillna(0)
energy["BTU"] = pd.to_numeric(energy["BTU"], errors="coerce").fillna(0)
energy["Cost_per_kWh"] = pd.to_numeric(energy["Cost_per_kWh"], errors="coerce").fillna(0)

# ---------------- DEFAULT LOGIN USER ---------------- #
if users.empty:
    users.loc[len(users)] = ["admin","Admin","admin123","Admin"]
    users.to_csv(os.path.join(DATA_PATH,"users.csv"), index=False)

# ---------------- LOGIN ---------------- #
st.sidebar.title("🔐 Login")

username = st.sidebar.text_input("User ID")
password = st.sidebar.text_input("Password", type="password")

if st.sidebar.button("Login"):
    user = users[(users["Employee_ID"] == username) & (users["Password"] == password)]
    if not user.empty:
        st.session_state["logged_in"] = True
        st.session_state["user"] = user.iloc[0]["Name"]
        st.session_state["role"] = user.iloc[0]["Role"]
    else:
        st.sidebar.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.stop()

st.sidebar.success(f"Welcome {st.session_state['user']}")

menu = st.sidebar.radio("Navigation", [
    "Wall Dashboard",
    "Assets",
    "Energy",
    "AMC Management",
    "PDF Report"
])

# ======================================================
# 1️⃣ WALL DASHBOARD
# ======================================================
if menu == "Wall Dashboard":
    st.title("🏢 All HVAC On One Screen")

    total_assets = len(assets)
    attention = len(assets[assets["Health"]=="Attention"])
    ok_assets = len(assets[assets["Health"]=="OK"])

    total_kwh = energy["kWh"].sum()
    total_btu = energy["BTU"].sum()
    total_cost = (energy["kWh"] * energy["Cost_per_kWh"]).sum()

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Total Assets", total_assets)
    col2.metric("Attention Required", attention)
    col3.metric("Energy (kWh)", f"{total_kwh:,.0f}")
    col4.metric("Energy Cost ₹", f"{total_cost:,.0f}")

    st.dataframe(assets, use_container_width=True)

# ======================================================
# 2️⃣ ASSETS
# ======================================================
elif menu == "Assets":
    st.title("HVAC Asset Management")

    with st.form("asset_form"):
        asset_id = st.text_input("Asset ID")
        asset_name = st.text_input("Asset Name")
        asset_type = st.text_input("Asset Type")
        location = st.text_input("Location")
        health = st.selectbox("Health", ["OK","Attention"])
        vendor = st.text_input("AMC Vendor")
        amc_date = st.date_input("AMC End Date")
        submit = st.form_submit_button("Save")

    if submit:
        new_asset = {
            "Asset_ID": asset_id,
            "Asset_Name": asset_name,
            "Asset_Type": asset_type,
            "Location": location,
            "Health": health,
            "AMC_Vendor": vendor,
            "AMC_End_Date": amc_date
        }
        assets = pd.concat([assets, pd.DataFrame([new_asset])], ignore_index=True)
        assets.to_csv(os.path.join(DATA_PATH,"assets.csv"), index=False)
        st.success("Asset Added")

    st.dataframe(assets, use_container_width=True)

# ======================================================
# 3️⃣ ENERGY
# ======================================================
elif menu == "Energy":
    st.title("Energy + BTU Monitoring")

    with st.form("energy_form"):
        asset = st.selectbox("Asset", assets["Asset_ID"])
        kwh = st.number_input("kWh", min_value=0.0)
        btu = st.number_input("BTU", min_value=0.0)
        cost = st.number_input("Cost per kWh ₹", min_value=0.0)
        submit = st.form_submit_button("Submit")

    if submit:
        new_energy = {
            "Date": datetime.now().date(),
            "Asset_ID": asset,
            "kWh": kwh,
            "BTU": btu,
            "Cost_per_kWh": cost
        }
        energy = pd.concat([energy, pd.DataFrame([new_energy])], ignore_index=True)
        energy.to_csv(os.path.join(DATA_PATH,"energy.csv"), index=False)
        st.success("Energy Data Added")

    st.dataframe(energy, use_container_width=True)

# ======================================================
# 4️⃣ AMC MANAGEMENT
# ======================================================
elif menu == "AMC Management":
    st.title("AMC Vendor Tracking")

    today = datetime.now().date()
    assets["AMC_End_Date"] = pd.to_datetime(assets["AMC_End_Date"], errors="coerce")

    expiring = assets[assets["AMC_End_Date"] <= pd.Timestamp(today)]

    if not expiring.empty:
        st.error("⚠ AMC Expired / Due")
        st.dataframe(expiring)
    else:
        st.success("All AMC Valid")

# ======================================================
# 5️⃣ PDF REPORT
# ======================================================
elif menu == "PDF Report":
    st.title("Download Monthly PDF Report")

    if st.button("Generate PDF"):
        filename = "HVAC_Report.pdf"
        doc = SimpleDocTemplate(filename)
        elements = []

        styles = getSampleStyleSheet()
        elements.append(Paragraph("DLF HVAC Monthly Report", styles["Heading1"]))
        elements.append(Spacer(1,0.3*inch))

        elements.append(Paragraph(f"Total Assets: {len(assets)}", styles["Normal"]))
        elements.append(Paragraph(f"Total Energy: {energy['kWh'].sum()} kWh", styles["Normal"]))
        elements.append(Paragraph(f"Total Cost: ₹ {(energy['kWh']*energy['Cost_per_kWh']).sum()}", styles["Normal"]))

        doc.build(elements)

        with open(filename,"rb") as f:
            st.download_button("Download Report", f, file_name=filename)

        st.success("PDF Generated")
