import streamlit as st
import os
from supabase import create_client

# --- Funções de Conexão ---
def get_supabase():
    # Certifique-se de que SUPABASE_URL e SUPABASE_KEY estão no secrets.toml
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- Funções de Dados ---
def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    response = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return response.data

def resetar_lancamentos(user_id):
    supabase = get_supabase()
    return supabase.table("lancamentos").delete().eq("user_id", user_id).execute()

def deletar_lancamento_por_id(id):
    supabase = get_supabase()
    return supabase.table("lancamentos").delete().eq("id", id).execute()

# --- Funções de Interface ---
def check_auth():
    if "user" not in st.session_state:
        st.error("Usuário não autenticado.")
        st.stop()

def inject_css(file_name="style.css"):
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, dataframe):
    # Retorna bytes para evitar o erro do st.download_button
    conteudo = f"Relatório: {titulo}\n\nDados: {str(dataframe)}"
    return conteudo.encode('utf-8')
