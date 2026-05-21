import streamlit as st, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth(); inject_css()
st.header("📦 Estoque")
# (Cole aqui sua lógica original da aba Estoque)
