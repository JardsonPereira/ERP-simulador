import streamlit as st
from utils import get_supabase, inject_css

st.set_page_config(page_title="ERP Didático", layout="wide", page_icon="📊")
inject_css()
supabase = get_supabase()

if 'user' not in st.session_state:
    st.title("🔐 Login / Cadastro")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    username = st.text_input("Nome de Usuário")
    col1, col2 = st.columns(2)
    
    if col1.button("Cadastrar"):
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute()
            st.success("Conta criada! Faça login.")
            
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e: st.error(f"Falha: {e}")
else:
    st.title(f"Bem-vindo, {st.session_state.user.email}")
    st.write("Selecione uma opção no menu lateral para começar a gerenciar sua empresa.")
