import streamlit as st

def load_theme():
    st.markdown("""
    <style>
    .stApp {
        background-color: #0b1c2d;
        color: white;
    }
    h1, h2, h3 {
        color: gold;
    }
    .stMetric {
        background: #132f4c;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)
