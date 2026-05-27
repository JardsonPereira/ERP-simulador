import streamlit as st
import os
from supabase import create_client

# Inicialização do Cliente Supabase
def get_supabase():
    """Retorna a instância do cliente Supabase usando segredos."""
    return create_client(
        st.secrets["SUPABASE_URL"], 
        st.secrets["SUPABASE_KEY"]
    )

# Verificação de Autenticação
def check_auth():
    """
    Verifica se existe um usuário no session_state.
    Se não, redireciona para a página principal (login).
    """
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.switch_page("app.py")
        st.stop()
    return st.session_state["user"]

# Sidebar de Autenticação
def show_auth_sidebar(supabase):
    """Exibe o status do usuário logado e o botão de logout na sidebar."""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        
        # Lida com o objeto user sendo um objeto ou dicionário
        email = getattr(user, 'email', None) or (user.get('email') if isinstance(user, dict) else "Usuário")
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Logado como:**")
        st.sidebar.caption(email)
        
        if st.sidebar.button("🚪 Deslogar"):
            supabase.auth.sign_out()
            st.session_state["user"] = None
            st.switch_page("app.py")
            st.rerun()

# Injeção de CSS
def inject_css(file_name="style.css"):
    """Lê um arquivo CSS e aplica ao Streamlit."""
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
