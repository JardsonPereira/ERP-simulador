import streamlit as st
import os
from supabase import create_client

def get_supabase():
    # Certifique-se que SUPABASE_URL e SUPABASE_KEY estão no secrets.toml
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def check_auth():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    user = st.session_state["user"]
    # Tenta obter o ID tanto se for dicionário quanto objeto (Pydantic)
    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    
    if not user_id:
        st.error("Erro na sessão.")
        st.stop()
    return user_id

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
