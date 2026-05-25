import streamlit as st
import os
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

def show_sidebar(supabase):
    """Exibe o usuário logado e o botão de logout na barra lateral."""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        # Tenta pegar o email (seja objeto ou dicionário)
        email = getattr(user, 'email', None) or (user.get('email') if isinstance(user, dict) else "Usuário")
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Logado como:**")
        st.sidebar.caption(email)
        
        if st.sidebar.button("🚪 Deslogar"):
            supabase.auth.sign_out()
            st.session_state["user"] = None
            st.rerun()

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
