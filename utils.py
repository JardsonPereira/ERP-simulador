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
    """import streamlit as st
import os
from supabase import create_client
import pandas as pd

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    response = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return response.data

def check_auth():
    # Verifica se o usuário existe
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    user = st.session_state["user"]
    
    # Tenta extrair o ID de forma segura (funciona para dict ou objeto)
    if isinstance(user, dict):
        user_id = user.get("id")
    else:
        user_id = getattr(user, "id", None)
        
    if not user_id:
        st.error("Erro ao identificar ID do usuário.")
        st.stop()
        
    return user_id

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    Verifica se o usuário está logado e retorna o ID de forma segura,
    independentemente de ser um dicionário ou um objeto Supabase.
    """
    # 1. Verifica se a chave 'user' existe
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    user = st.session_state["user"]
    user_id = None

    # 2. Tenta extrair o ID dependendo do tipo de objeto
    if isinstance(user, dict):
        # Se for um dicionário, usa .get()
        user_id = user.get("id")
    else:
        # Se for um objeto (caso do Supabase/Pydantic), usa o atributo .id
        user_id = getattr(user, "id", None)

    # 3. Validação final
    if not user_id:
        st.error("Erro: Não foi possível obter o ID do usuário (sessão inválida).")
        st.stop()
        
    return user_id

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, dataframe):
    conteudo = f"Relatório: {titulo}\n\nDados: {str(dataframe)}"
    return conteudo.encode('utf-8')
