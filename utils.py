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
    Verifica se o usuário está logado de forma segura.
    Retorna o ID do usuário se estiver tudo ok, ou para o script se não estiver.
    """
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    # Retorna o ID de forma segura
    return st.session_state["user"].get("id")

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, dataframe):
    conteudo = f"Relatório: {titulo}\n\nDados: {str(dataframe)}"
    return conteudo.encode('utf-8')
