import streamlit as st
from utils import get_supabase

supabase = get_supabase()

st.title("🔐 Acesso ao Sistema")

# Se o usuário já estiver logado, redireciona direto para o app
if "user" in st.session_state and st.session_state["user"]:
    st.switch_page("pages/01_Lancamentos.py")

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
                st.switch_page("pages/01_Lancamentos.py")
        except Exception as e:
            st.error("Email ou senha inválidos.")

with tab2:
    st.subheader("Cadastrar-se")
    email_cad = st.text_input("Email", key="cad_email")
    password_cad = st.text_input("Senha", type="password", key="cad_pass")
    
    if st.button("Criar Conta"):
        try:
            response = supabase.auth.sign_up({"email": email_cad, "password": password_cad})
            st.success("Conta criada! Verifique seu e-mail.")
        except Exception as e:
            st.error(f"Erro no cadastro: {e}")
