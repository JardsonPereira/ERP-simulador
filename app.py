import streamlit as st
from supabase import create_client

# CONFIGURAÇÃO DIRETA COM SUAS CHAVES
URL = "https://ejdvfuczdnpyhuosruey.supabase.co"
KEY = "sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"

supabase = create_client(URL, KEY)

st.set_page_config(page_title="Sistema Contabil", layout="wide")

# Inicialização de estado
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    # Esconde o menu se não estiver logado
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    st.title("Sistema Contabil - Login")
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
            except Exception as e:
                st.error(f"Erro no login: {e}")

    with tab2:
        novo_email = st.text_input("Novo E-mail", key="c_email")
        nova_senha = st.text_input("Nova Senha", type="password", key="c_senha")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado! Verifique seu e-mail.")
            except Exception as e:
                st.error(f"Erro no cadastro: {e}")

if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.title("Menu Principal")
    st.write(f"Logado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.rerun()
