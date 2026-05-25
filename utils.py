import streamlit as st
import os
from supabase import create_client

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def check_auth():
    if "user" not in st.session_state or st.session_state["user"] is None:
        # Se não estiver logado, redireciona para a página principal (Login)
        st.switch_page("app.py")
        st.stop()
    return st.session_state["user"]

def show_auth_sidebar(supabase):
    """Exibe o usuário logado e o botão de logout na barra lateral."""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        email = getattr(user, 'email', None) or (user.get('email') if isinstance(user, dict) else "Usuário")
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Logado como:**")
        st.sidebar.caption(email)
        
        if st.sidebar.button("🚪 Deslogar"):
            supabase.auth.sign_out()
            st.session_state["user"] = None
            st.switch_page("app.py") # Volta para a tela de login
            st.rerun()

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
