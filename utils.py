import streamlit as st
from supabase import create_client

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

def check_auth():
    if "user" not in st.session_state:
        st.error("Usuário não autenticado.")
        st.stop()

def inject_css(file_name="style.css"):
    """
    Carrega e injeta um arquivo CSS no Streamlit.
    Certifique-se de ter um arquivo 'style.css' na mesma pasta.
    """
    try:
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Arquivo CSS '{file_name}' não encontrado.")
