import streamlit as st
from supabase import create_client
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Conexão
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="Sistema Contábil", layout="wide")

# Inicialização de estado
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title("Sistema Contábil - Login")
    tab1, tab2 = st.tabs(["Login", "Cadastrar"])
    with tab1:
        email = st.text_input("E-mail", key="l_email")
        senha = st.text_input("Senha", type="password", key="l_senha")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.logged_in = True
                st.session_state.user = res.user
                st.rerun()
            except Exception as e: st.error(f"Erro no login: {e}")
    with tab2:
        novo_email = st.text_input("Novo E-mail", key="c_email")
        nova_senha = st.text_input("Nova Senha", type="password", key="c_senha")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado! Verifique seu e-mail.")
            except Exception as e: st.error(f"Erro no cadastro: {e}")

# Lógica de Login
if not st.session_state.logged_in:
    login_page()
else:
    st.title("Bem-vindo ao Sistema Contábil")
    st.write("Use o menu lateral para navegar entre as seções (Lançamentos, Fluxo de Caixa, etc).")
    if st.button("Sair"):
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.rerun()
