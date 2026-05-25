import streamlit as st
from supabase import create_client

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def check_auth():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    user = st.session_state["user"]
    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    return user_id
