import streamlit as st
from supabase import create_client
import erp_functions

# Inicialização
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# Autenticação
if not st.session_state.user:
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("E-mail")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.sidebar.error("Login falhou.")
    st.stop()

# Área Logada
st.sidebar.write(f"Usuário: {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["🛒 Vendas", "⚙️ Gestão"])

if menu == "🛒 Vendas":
    erp_functions.mostrar_vendas_erp(supabase, st.session_state.user.id)
elif menu == "⚙️ Gestão":
    erp_functions.mostrar_gestao(supabase, st.session_state.user.id)
