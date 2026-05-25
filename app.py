import streamlit as st

# Configuração da página
st.set_page_config(page_title="Sistema Contabil", layout="wide")

# Inicializa o estado de login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    # CSS para ocultar a sidebar apenas quando não estiver logado
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Lógica de autenticação (substitua pela sua verificação real)
        if username == "admin" and password == "123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos")

def main_menu():
    st.title("Bem-vindo ao ContabilApp")
    st.write("Use o menu lateral para acessar os módulos.")
    
    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# Lógica de exibição
if not st.session_state.logged_in:
    login_page()
else:
    main_menu()
