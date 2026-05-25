import streamlit as st
import os
from supabase import create_client

# --- Funções de Conexão e Banco de Dados ---

def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

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

# --- Funções de Interface e Autenticação ---

def check_auth():
    if "user" not in st.session_state:
        st.error("Usuário não autenticado.")
        st.stop()

def inject_css(file_name="style.css"):
    """
    Carrega e injeta um arquivo CSS no Streamlit.
    Verifica se o arquivo existe para não exibir avisos de erro.
    """
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Função de PDF (Corrigida para retornar bytes) ---

def gerar_relatorio_pdf(titulo, dataframe):
    """
    Gera um placeholder de relatório PDF.
    Retorna bytes para que o botão de download funcione sem erros.
    """
    # No futuro, aqui você usará a biblioteca FPDF para criar o PDF real.
    # Por enquanto, retornamos bytes vazios para satisfazer o st.download_button.
    conteudo = f"Relatório: {titulo}\n\nDados: {str(dataframe)}"
    return conteudo.encode('utf-8')
