import streamlit as st
from supabase import create_client

def get_supabase():
    # As chaves devem estar no .streamlit/secrets.toml
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    # Busca apenas dados do usuário logado
    response = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return response.data

def resetar_lancamentos(user_id):
    supabase = get_supabase()
    return supabase.table("lancamentos").delete().eq("user_id", user_id).execute()

def deletar_lancamento_por_id(id):
    supabase = get_supabase()
    return supabase.table("lancamentos").delete().eq("id", id).execute()
