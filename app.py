import streamlit as st
from utils import get_supabase

supabase = get_supabase()

st.title("🔐 Acesso ao Sistema")

if "user" in st.session_state and st.session_state["user"]:
    st.switch_page("pages/01_Lancamentos.py")

tab1, tab2 = st.tabs(["Login", "Cadastrar-se"])

with tab1:
    email = st.text_input("Email", key="l_email")
    password = st.text_input("Senha", type="password", key="l_pass")
    if st.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.user:
                st.session_state["user"] = res.user
                st.switch_page("pages/01_Lancamentos.py")
        except:
            st.error("Credenciais inválidas.")

with tab2:
    email_c = st.text_input("Email", key="c_email")
    password_c = st.text_input("Senha", type="password", key="c_pass")
    if st.button("Criar Conta"):
        try:
            supabase.auth.sign_up({"email": email_c, "password": password_c})
            st.success("Conta criada! Verifique seu e-mail.")
        except Exception as e:
            st.error(str(e))
