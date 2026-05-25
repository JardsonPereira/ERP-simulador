import streamlit as st
from utils import get_supabase

# Inicializar Supabase
supabase = get_supabase()

st.title("🔐 Acesso ao Sistema")

# Aba de Login e Cadastro
tab1, tab2 = st.tabs(["Login", "Cadastrar-se"])

with tab1:
    st.subheader("Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Senha", type="password", key="login_pass")
    
    if st.button("Entrar"):
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                st.session_state["user"] = response.user
                st.success("Login efetuado com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro no login: {e}")

with tab2:
    st.subheader("Novo Usuário")
    email_cad = st.text_input("Email", key="cad_email")
    password_cad = st.text_input("Senha", type="password", key="cad_pass")
    
    if st.button("Criar Conta"):
        try:
            # O cadastro no Supabase não escreve diretamente nas suas tabelas,
            # ele cria um user na auth schema.
            response = supabase.auth.sign_up({"email": email_cad, "password": password_cad})
            st.success("Conta criada! Verifique o seu email para confirmar.")
        except Exception as e:
            st.error(f"Erro no cadastro: {e}")
