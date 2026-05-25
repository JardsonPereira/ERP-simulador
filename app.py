import streamlit as st
from supabase import create_client

# Configurações do Supabase (certifique-se de ter essas chaves no seu .streamlit/secrets.toml)
SUPABASE_URL="https://ejdvfuczdnpyhuosruey.supabase.co"
SUPABASE_KEY="sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Sistema Contabil", layout="wide")

# Inicialização de estado para evitar erros de AttributeError
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = None

def login_page():
    # CSS para ocultar a sidebar durante o login
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    st.title("Sistema Contabil - Acesso")
    
    # DEFINIÇÃO DAS ABAS: Criar antes de chamar with tab1/tab2
    tab1, tab2 = st.tabs(["Login", "Cadastrar"])
    
    with tab1:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar"):
            try:
                response = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.logged_in = True
                st.session_state.user = response.user.email
                st.rerun()
            except Exception:
                st.error("E-mail ou senha incorretos.")

    with tab2:
        novo_email = st.text_input("Novo E-mail", key="cad_email")
        nova_senha = st.text_input("Nova Senha", type="password", key="cad_senha")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado! Verifique seu e-mail.")
            except Exception:
                st.error("Erro no cadastro.")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # A sidebar aparece automaticamente aqui pois o CSS de ocultação não é carregado
        st.sidebar.title("Menu Principal")
        st.write(f"Bem-vindo ao seu ERP, {st.session_state.user}!")
        
        if st.sidebar.button("Sair"):
            supabase.auth.sign_out()
            st.session_state.logged_in = False
            st.session_state.user = None
            st.rerun()

if __name__ == "__main__":
    main()
