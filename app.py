import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==================================
# DLF Enterprise Control Room V6 - Full Expanded & Auto-refresh Fixed
# ==================================

st.set_page_config(page_title='DLF Enterprise Control Room V6', layout='wide', page_icon='🏢')
st.markdown("""
<style>
body { background-color: #0a0f17; color: #FFFFFF; }
.sidebar .sidebar-content { background-color: #0a0f17; }
h1, h2, h3, h4, h5, h6 { color: #00FFFF; }
div.stButton > button:first-child { background-color: #00FFFF; color:#000000; }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Users and Roles
# -------------------------
users = {
    'admin': {'password': 'admin123', 'role': 'Admin'},
    'exec': {'password': 'exec123', 'role': 'Executive'},
    'eng': {'password': 'eng123', 'role': 'Engineer'}
}
roles = ['Admin', 'Executive', 'Engineer']
departments = ['HVAC','DG','Electrical','STP','WTP','Lifts','CCTV','Fire','Facade','BMS','Compliance']

# -------------------------
# Login
# -------------------------
st.title('DLF Enterprise Control Room V6 Login')
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

# -------------------------
# Utility functions for dummy data
# -------------------------
def create_assets(dept):
    return pd.DataFrame({'Asset':[f'{dept}_Asset_{i}' for i in range(1,11)],
                         'Status':np.random.choice(['Good','Warning','Critical'],10),
                         'Criticality':np.random.randint(1,5,10)})

def create_energy(dept):
    return pd.DataFrame({'Date':pd.date_range(end=datetime.today(), periods=30),
                         'Consumption':np.random.randint(100,500,30)})

def create_budget(dept):
    return pd.DataFrame({'Category':['Maintenance','IT','Security','Energy'],
                         'Budget':np.random.randint(50000,200000,4),
                         'Spent':np.random.randint(30000,180000,4)})

def create_vendor(dept):
    return pd.DataFrame({'Vendor':[f'{dept}_Vendor_{i}' for i in range(1,6)],
                         'Score':np.random.randint(60,100,5)})

def create_alerts(dept):
    return pd.DataFrame({'Alert':[f'{dept} Alert {i}' for i in range(1,4)],
                         'Severity':np.random.choice(['Low','Medium','High'],3)})

def create_predictive(dept):
    return pd.DataFrame({'KPI':['Energy Forecast','Budget Forecast','Vendor Risk'],
                         'Value':[np.random.randint(100,500), np.random.randint(30000,180000), np.random.randint(60,100)]})

def create_risk(dept):
    return pd.DataFrame({'Parameter':['Asset','Energy','Budget','Vendor'],
                         'Risk Level':np.random.choice(['Low','Medium','High'],4)})

# -------------------------
# PDF Export
# -------------------------
def export_pdf(dept, assets, energy, budget, vendor, alerts, predictive, risk):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial','B',16)
    pdf.cell(0,10,f'{dept} Executive Report', ln=True, align='C')
    pdf.ln(10)
    pdf.set_font('Arial','',12)

    for label, df in [('Assets', assets), ('Energy', energy), ('Budget', budget), ('Vendor Scores', vendor), ('Alerts', alerts), ('Predictive KPIs', predictive), ('Risk Matrix', risk)]:
        pdf.cell(0,10,f'{label}:', ln=True)
        for i,row in df.iterrows():
            pdf.cell(0,8,' - '.join([str(v) for v in row.values]), ln=True)
        pdf.ln(5)

    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    return output

# -------------------------
# Dashboard Wall + Department Sections
# -------------------------
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    role = st.session_state['role']

    # Auto-refresh every 10 sec
    st_autorefresh(interval=10000, key="global_refresh")

    col1, col2, col3 = st.columns([1,6,1])
    with col1:
        st.image('https://via.placeholder.com/120x60?text=DLF', width=120)
    with col2:
        st.markdown('<h1 style="text-align:center;color:#00FFFF;">DLF Enterprise Control Room V6</h1>', unsafe_allow_html=True)
    with col3:
        st.image('https://via.placeholder.com/120x60?text=LNP', width=120)

    st.markdown('---')

    st.subheader('Departments')
    dept_cols = st.columns(len(departments))
    for i, dept in enumerate(departments):
        if dept_cols[i].button(dept):
            st.session_state['selected_dept'] = dept

# -------------------------
# Fully expanded department section template (repeat for each dept)
# -------------------------
if 'selected_dept' in st.session_state:
    dept = st.session_state['selected_dept']
    st.subheader(f'{dept} Dashboard')

    assets = create_assets(dept)
    energy = create_energy(dept)
    budget = create_budget(dept)
    vendor = create_vendor(dept)
    alerts = create_alerts(dept)
    predictive = create_predictive(dept)
    risk = create_risk(dept)

    # KPI Cards
    kpi_cols = st.columns(5)
    dept_kpis = {
        'Total Assets': len(assets),
        'Critical Assets': sum(assets.Status=='Critical'),
        'Budget Used %': f'{int(budget.Spent.sum()/budget.Budget.sum()*100)}%',
        'Avg Vendor Score': int(vendor.Score.mean()),
        'Active Alerts': len(alerts)
    }
    colors=['#39FF14','#FF3131','#FFFB00','#00FFFF','#FF6EC7']
    for i,(k,v) in enumerate(dept_kpis.items()):
        kpi_cols[i].markdown(f"""
            <div style='background-color:#111827;border-radius:12px;padding:20px;text-align:center;'>
                <h4 style='color:{colors[i]};'>{k}</h4>
                <h3 style='color:{colors[i]};'>{v}</h3>
            </div>
        """, unsafe_allow_html=True)

    # Charts
    col1,col2 = st.columns(2)
    with col1:
        fig_energy = px.line(energy, x='Date', y='Consumption', title=f'Energy Trend {dept}', template='plotly_dark')
        st.plotly_chart(fig_energy, use_container_width=True)
    with col2:
        fig_vendor = px.bar(vendor, x='Vendor', y='Score', title=f'Vendor Scores {dept}', template='plotly_dark')
        st.plotly_chart(fig_vendor, use_container_width=True)

    # Risk Matrix
    st.subheader('Risk Matrix')
    def risk_color(r): return 'red' if r=='High' else 'yellow' if r=='Medium' else 'green'
    risk_display = risk.style.applymap(lambda x: f'color: {risk_color(x)}', subset=['Risk Level'])
    st.dataframe(risk_display)

    # Export Buttons
    col_exp1,col_exp2 = st.columns(2)
    with col_exp1:
        csv_data = pd.concat([assets, energy, budget, vendor, alerts], axis=1).to_csv().encode('utf-8')
        st.download_button(f'Export CSV {dept}', data=csv_data, file_name=f'{dept}_data.csv', mime='text/csv')
    with col_exp2:
        pdf_file = export_pdf(dept, assets, energy, budget, vendor, alerts, predictive, risk)
        st.download_button(f'Export PDF {dept}', data=pdf_file, file_name=f'{dept}_report.pdf')
