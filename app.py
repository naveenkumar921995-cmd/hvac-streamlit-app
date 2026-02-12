import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# ------------------------
# Dummy Data Simulation
# ------------------------
departments = ['Facilities', 'Security', 'IT', 'Energy', 'Admin']
roles = ['Admin', 'Executive', 'Engineer']

# Simulate Users
users = {
    'admin': {'password': 'admin123', 'role': 'Admin'},
    'exec': {'password': 'exec123', 'role': 'Executive'},
    'eng': {'password': 'eng123', 'role': 'Engineer'}
}

# Simulate Department Data
def generate_department_data(dept):
    np.random.seed(int(time.time()) % 1000)
    assets = pd.DataFrame({
        'Asset': [f'{dept}_Asset_{i}' for i in range(1, 11)],
        'Status': np.random.choice(['Good', 'Warning', 'Critical'], 10),
        'Criticality': np.random.randint(1, 5, 10)
    })
    energy = pd.DataFrame({
        'Date': pd.date_range(end=datetime.today(), periods=30),
        'Consumption': np.random.randint(100, 500, 30)
    })
    budget = pd.DataFrame({
        'Category': ['Maintenance', 'IT', 'Security', 'Energy'],
        'Budget': np.random.randint(50000, 200000, 4),
        'Spent': np.random.randint(30000, 180000, 4)
    })
    vendor_scores = pd.DataFrame({
        'Vendor': [f'{dept}_Vendor_{i}' for i in range(1, 6)],
        'Score': np.random.randint(60, 100, 5)
    })
    alerts = pd.DataFrame({
        'Alert': [f'{dept} Alert {i}' for i in range(1, 4)],
        'Severity': np.random.choice(['Low', 'Medium', 'High'], 3)
    })
    return assets, energy, budget, vendor_scores, alerts

# ------------------------
# PDF Export Function
# ------------------------
def generate_pdf(dept, assets, energy, budget, vendor_scores, alerts):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{dept} Department Report', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'Assets:', ln=True)
    for i, row in assets.iterrows():
        pdf.cell(0, 8, f'{row.Asset} - {row.Status} - Criticality {row.Criticality}', ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, 'Budget:', ln=True)
    for i, row in budget.iterrows():
        pdf.cell(0, 8, f'{row.Category} - Budget: {row.Budget} - Spent: {row.Spent}', ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, 'Vendor Scores:', ln=True)
    for i, row in vendor_scores.iterrows():
        pdf.cell(0, 8, f'{row.Vendor} - Score: {row.Score}', ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, 'Alerts:', ln=True)
    for i, row in alerts.iterrows():
        pdf.cell(0, 8, f'{row.Alert} - Severity: {row.Severity}', ln=True)

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

# ------------------------
# Streamlit App
# ------------------------

st.set_page_config(page_title='DLF Cyberpark Management Dashboard', layout='wide')

# Ultra-dark theme
st.markdown("""
<style>
body { background-color: #0e1117; color: #FFFFFF; }
.sidebar .sidebar-content { background-color: #111317; }
h1, h2, h3, h4, h5, h6 { color: #00FFFF; }
</style>
""", unsafe_allow_html=True)

# ------------------------
# Login Page
# ------------------------
st.title('DLF Cyberpark Management Dashboard Login')
username = st.text_input('Username')
password = st.text_input('Password', type='password')

if st.button('Login'):
    if username in users and password == users[username]['password']:
        st.session_state['logged_in'] = True
        st.session_state['role'] = users[username]['role']
        st.session_state['username'] = username
        st.experimental_rerun()
    else:
        st.error('Invalid username or password')

# ------------------------
# Main App
# ------------------------
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    role = st.session_state['role']
    st.session_state['role'] = role

    # Header with logos
    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        st.image('https://via.placeholder.com/100x50?text=DLF', width=100)
    with col2:
        st.markdown('<h1 style="text-align:center; color:#00FFFF;">DLF Cyberpark Management Dashboard</h1>', unsafe_allow_html=True)
    with col3:
        st.image('https://via.placeholder.com/100x50?text=LNP', width=100)

    st.markdown('---')

    # Main KPIs simulation
    kpi_cols = st.columns(5)
    kpis = {
        'System Health': f'{np.random.randint(85,100)}%',
        'Risk Level': f'{np.random.randint(1,5)}/5',
        'Asset Criticality': f'{np.random.randint(1,5)}/5',
        'Energy Spike': f'{np.random.randint(0,20)}%',
        'Budget Deviation': f'{np.random.randint(0,15)}%'
    }
    colors = ['#39FF14', '#FF3131', '#FFFB00', '#00FFFF', '#FF6EC7']
    for i, (k, v) in enumerate(kpis.items()):
        kpi_cols[i].markdown(f"""
            <div style='background-color:#1C1C1C; border-radius:10px; padding:20px; text-align:center;'>
                <h3 style='color:{colors[i]};'>{k}</h3>
                <h2 style='color:{colors[i]};'>{v}</h2>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('---')

    # Department Selection
    st.subheader('Departments')
    dept_cols = st.columns(len(departments))
    for i, dept in enumerate(departments):
        if dept_cols[i].button(dept):
            st.session_state['selected_dept'] = dept

    # Department Dashboard
    if 'selected_dept' in st.session_state:
        dept = st.session_state['selected_dept']
        st.subheader(f'{dept} Department Dashboard')

        assets, energy, budget, vendor_scores, alerts = generate_department_data(dept)

        # KPIs
        dept_kpi_cols = st.columns(5)
        dept_kpis = {
            'Total Assets': len(assets),
            'Critical Assets': sum(assets['Status']=='Critical'),
            'Budget Used %': f'{int(budget.Spent.sum()/budget.Budget.sum()*100)}%',
            'Average Vendor Score': int(vendor_scores.Score.mean()),
            'Active Alerts': len(alerts)
        }
        for i, (k,v) in enumerate(dept_kpis.items()):
            dept_kpi_cols[i].markdown(f"""
                <div style='background-color:#1C1C1C; border-radius:10px; padding:15px; text-align:center;'>
                    <h4 style='color:#39FF14;'>{k}</h4>
                    <h3 style='color:#39FF14;'>{v}</h3>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('---')

        # Charts
        col1, col2 = st.columns(2)
        with col1:
            fig_energy = px.line(energy, x='Date', y='Consumption', title='Energy Consumption Trend', template='plotly_dark')
            st.plotly_chart(fig_energy, use_container_width=True)
        with col2:
            fig_vendor = px.bar(vendor_scores, x='Vendor', y='Score', title='Vendor Scores', template='plotly_dark')
            st.plotly_chart(fig_vendor, use_container_width=True)

        # Export Buttons
        col_export1, col_export2 = st.columns(2)
        with col_export1:
            csv = pd.concat([assets, energy, budget, vendor_scores, alerts], axis=1).to_csv().encode('utf-8')
            st.download_button(label='Export CSV', data=csv, file_name=f'{dept}_data.csv', mime='text/csv')
        with col_export2:
            pdf_file = generate_pdf(dept, assets, energy, budget, vendor_scores, alerts)
            st.download_button(label='Export PDF', data=pdf_file, file_name=f'{dept}_report.pdf')

        # Auto-refresh every 10 seconds
        st.experimental_rerun()  # Simple auto-refresh simulation
