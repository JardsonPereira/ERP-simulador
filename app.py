import streamlit as st
from supabase import create_client

# Configurações do Supabase (use os dados do seu painel)
# Dica: Coloque essas chaves no arquivo .streamlit/secrets.toml
SUPABASE_URL="https://ejdvfuczdnpyhuosruey.supabase.co"
SUPABASE_KEY="sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configuração da página
st.set_page_config(page_title="Sistema Contabil", layout="wide")

# Inicializa estado
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    # Oculta o menu lateral no login
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    st.title("Acesso ao Sistema")
    tab1, tab2 = st.tabs(["Login", "Cadastrar"])
    
    with tab1:
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.logged_in = True
                st.session_state.user = response.user.email
                st.rerun()
            except Exception as e:
                st.error("Erro no login: Verifique e-mail e senha.")

    with tab2:
        novo_email = st.text_input("Novo E-mail")
        nova_senha = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado! O Trigger do banco irá criar seu perfil automaticamente.")
            except Exception as e:
                st.error("Erro no cadastro.")

def main():
    if not st.session_state.get('logged_in', False):
        login_page()
    else:
        st.sidebar.title("Menu Principal")
        # Usamos .get() para evitar o erro AttributeError
        usuario_atual = st.session_state.get('user', 'Usuário')
        st.write(f"Bem-vindo, {usuario_atual}!")
        
        if st.sidebar.button("Sair"):
            supabase.auth.sign_out()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()
