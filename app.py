import os
import sqlite3

# Adicione isso logo abaixo dos seus imports
print(f"O banco de dados está sendo lido em: {os.path.abspath('usuarios.db')}")
import streamlit as st
import sqlite3
import os

# Configuração da página
st.set_page_config(page_title="Sistema Contabil", layout="wide")

# --- BANCO DE DADOS LOCAL (SQLite) ---
def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- LÓGICA DE LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    # Esconde o menu lateral enquanto não estiver logado
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    st.title("Login de Acesso")
    
    tab1, tab2 = st.tabs(["Login", "Cadastrar Novo Usuário"])
    
    with tab1:
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            conn = sqlite3.connect('usuarios.db')
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
            if c.fetchone():
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
            conn.close()

    with tab2:
        new_user = st.text_input("Novo Usuário")
        new_pw = st.text_input("Nova Senha", type="password")
        if st.button("Cadastrar"):
            conn = sqlite3.connect('usuarios.db')
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users VALUES (?, ?)", (new_user, new_pw))
                conn.commit()
                st.success("Conta criada! Vá para a aba Login.")
            except:
                st.warning("Usuário já existe.")
            conn.close()

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.title("Menu Principal")
        st.write("Bem-vindo ao Sistema Contabil!")
        if st.sidebar.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
