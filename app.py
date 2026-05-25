import streamlit as st
import sqlite3
import os

# Configuração da página
st.set_page_config(page_title="Sistema Contabil", layout="wide")

# --- BANCO DE DADOS ---
def get_db_path():
    return os.path.join(os.getcwd(), 'usuarios.db')

def init_db():
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

def carregar_usuarios():
    try:
        conn = sqlite3.connect(get_db_path())
        c = conn.cursor()
        c.execute("SELECT username, password FROM users")
        # Criar dicionário garantindo que strings estejam limpas
        dados = {str(row[0]).strip(): str(row[1]).strip() for row in c.fetchall()}
        conn.close()
        return dados
    except Exception as e:
        st.error(f"Erro ao acessar banco: {e}")
        return {}

def cadastrar_usuario(user, pw):
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.strip(), pw.strip()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Inicialização
init_db()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- INTERFACES ---
def login_page():
    # CSS para ocultar a sidebar apenas no login
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    st.title("Login de Acesso")
    usuarios_bd = carregar_usuarios()
    
    tab1, tab2 = st.tabs(["Login", "Cadastrar Novo Usuário"])
    
    with tab1:
        st.subheader("Autenticação")
        user_input = st.text_input("Usuário")
        pw_input = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            u_in = str(user_input).strip()
            p_in = str(pw_input).strip()
            
            # Verificação contra o banco
            if u_in in usuarios_bd and usuarios_bd[u_in] == p_in:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
                st.info(f"Usuários encontrados no banco: {list(usuarios_bd.keys())}")
                
    with tab2:
        st.subheader("Novo Cadastro")
        new_user = st.text_input("Novo Usuário")
        new_pw = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            if cadastrar_usuario(new_user, new_pw):
                st.success("Cadastro realizado! Faça o login.")
                st.rerun()
            else:
                st.warning("Este usuário já existe no banco.")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.title("Menu Principal")
        st.write("Bem-vindo ao ContabilApp!")
        if st.sidebar.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
