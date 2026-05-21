import streamlit as st
from supabase import create_client
from erp_functions import mostrar_vendas_erp, mostrar_gestao

# Inicialização
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- LÓGICA DE AUTENTICAÇÃO (O que estava faltando) ---
if 'user' not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.sidebar.title("🔐 Acesso")
    menu_auth = st.sidebar.radio("Escolha", ["Login", "Criar Conta"])
    email = st.sidebar.text_input("E-mail").lower().strip()
    senha = st.sidebar.text_input("Senha", type="password")
    
    if st.sidebar.button("Confirmar"):
        try:
            if menu_auth == "Login":
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.user = res.user
            else:
                supabase.auth.sign_up({"email": email, "password": senha})
                st.success("Conta criada! Agora faça o login.")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")
    st.stop() # Bloqueia o resto do código se não estiver logado

# --- SE O USUÁRIO ESTIVER LOGADO, MOSTRA O RESTO ---
st.sidebar.title("🏢 Menu ERP")
menu = st.sidebar.radio("Navegação", ["🛒 ERP/Vendas", "📊 Razonetes", "⚙️ Gestão"])
# ... (restante do roteamento)
