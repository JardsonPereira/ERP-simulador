import streamlit as st
import os
from supabase import create_client

def get_supabase():
    """
    Cria a conexão com o Supabase usando os segredos do Streamlit.
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro ao conectar ao Supabase: Verifique o seu secrets.toml. {e}")
        st.stop()

def check_auth():
    """
    Verifica se existe um utilizador na sessão. 
    Retorna o user_id de forma segura, seja um dicionário ou objeto.
    """
    # Verifica se o utilizador está na sessão
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado. Por favor, faça login.")
        st.stop()
    
    user = st.session_state["user"]
    
    # Extrai o ID de forma segura:
    # 1. Se for um objeto do Supabase/Pydantic, usa .id
    # 2. Se for um dicionário, usa .get("id")
    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    
    if not user_id:
        st.error("Erro na sessão: Não foi possível identificar o ID do usuário.")
        st.stop()
        
    return user_id

def inject_css(file_name="style.css"):
    """
    Aplica estilos CSS se o ficheiro existir na raiz.
    """
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
