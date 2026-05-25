import streamlit as st
import os
from supabase import create_client

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    response = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return response.data

def check_auth():
    """
    Verificação de segurança robusta:
    1. Verifica se o usuário existe no session_state.
    2. Identifica se é um dicionário ou um objeto Supabase para extrair o ID.
    """
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    user = st.session_state["user"]
    
    # Tenta extrair ID de forma segura
    if isinstance(user, dict):
        user_id = user.get("id")
    else:
        # Tenta aceder ao atributo .id (caso seja objeto Supabase)
        user_id = getattr(user, "id", None)
        
    if not user_id:
        st.error("Erro na sessão: ID de usuário não encontrado.")
        st.stop()
        
    return user_id

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, dataframe):
    conteudo = f"Relatório: {titulo}\n\nDados: {str(dataframe)}"
    return conteudo.encode('utf-8')
