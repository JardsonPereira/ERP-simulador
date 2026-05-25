import streamlit as st
import os
from supabase import create_client

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def check_auth():
    # Verifica autenticação de forma segura
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    user = st.session_state["user"]
    
    # Extrai o ID de forma segura (objeto ou dicionário)
    if isinstance(user, dict):
        user_id = user.get("id")
    else:
        user_id = getattr(user, "id", None)
    
    if not user_id:
        st.error("Erro na sessão.")
        st.stop()
    return user_id

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
