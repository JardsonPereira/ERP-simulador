import streamlit as st
from supabase import create_client

# Inicialize o cliente do Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def cadastrar_usuario(email, senha):
    # O Supabase cria o usuário na tabela auth.users automaticamente
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": senha
        })
        return response
    except Exception as e:
        return e

def login_usuario(email, senha):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": senha
        })
        return response
    except Exception as e:
        return e

# --- No seu formulário ---
with tab2: # Aba de Cadastro
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    if st.button("Cadastrar"):
        res = cadastrar_usuario(email, senha)
        st.success("Verifique seu e-mail para confirmar o cadastro!")
