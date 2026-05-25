import streamlit as st
import os
from supabase import create_client

# Configura conexão
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Função de Autenticação Robusta (Resolve erro de Pydantic/NoneType)
def check_auth():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.error("Usuário não autenticado.")
        st.stop()
    
    user = st.session_state["user"]
    # Tenta obter ID de forma segura (objeto ou dicionário)
    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    
    if not user_id:
        st.error("Erro ao identificar ID do usuário.")
        st.stop()
    return user_id

# Funções auxiliares mantidas
def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, dataframe):
    conteudo = f"Relatório: {titulo}\n\nDados: {str(dataframe)}"
    return conteudo.encode('utf-8')
