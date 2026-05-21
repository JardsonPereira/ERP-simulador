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

def check_auth():
    if "user" not in st.session_state:
        st.error("Usuário não autenticado.")
        st.stop()

def inject_css():
    st.markdown("""
        <style>
            .stApp { background-color: #f9f9f9; }
            .stButton>button { width: 100%; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)
