import streamlit as st
import sqlite3

# Configuração da página
st.set_page_config(page_title="Sistema Contabil", layout="wide")

# --- BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def carregar_usuarios():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("SELECT username, password FROM users")
    dados = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return dados

def cadastrar_usuario(user, pw):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Inicializa banco e estado
init_db()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- INTERFACES ---
def login_page():
    # Oculta o menu lateral
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    usuarios_bd = carregar_usuarios()
    
    tab1, tab2 = st.tabs(["Login", "Cadastrar Novo Usuário"])
    
    with tab1:
        st.subheader("Login")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if usuarios_bd.get(user) == pw:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
                
    with tab2:
        st.subheader("Novo Cadastro")
        new_user = st.text_input("Escolha um usuário")
        new_pw = st.text_input("Escolha uma senha", type="password")
        if st.button("Cadastrar"):
            if cadastrar_usuario(new_user, new_pw):
                st.success("Cadastro realizado com sucesso!")
                st.rerun()
            else:
                st.warning("Este usuário já existe!")

    with st.expander("Usuários já cadastrados no banco"):
        st.write(list(usuarios_bd.keys()))

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # Quando logado, a sidebar reaparece automaticamente
        st.sidebar.title("Menu Principal")
        st.write("Bem-vindo ao ContabilApp!")
        if st.sidebar.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
