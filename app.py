import streamlit as st
import sqlite3
import os

# Define o caminho absoluto para o banco de dados na mesma pasta do script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "usuarios.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.commit()
    conn.close()

# Garante que o banco exista ao iniciar
init_db()

# Inicializa estado
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    st.title("Login e Cadastro")
    
    tab1, tab2 = st.tabs(["Login", "Cadastrar"])
    
    with tab1:
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pw))
            if c.fetchone():
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário não encontrado.")
            conn.close()

    with tab2:
        new_user = st.text_input("Novo Usuário (E-mail)")
        new_pw = st.text_input("Nova Senha", type="password")
        if st.button("Salvar no Banco"):
            conn = sqlite3.connect(DB_PATH)
            try:
                conn.execute("INSERT INTO users VALUES (?, ?)", (new_user, new_pw))
                conn.commit()
                st.success("Usuário cadastrado com sucesso!")
            except:
                st.error("Erro: Este usuário já existe ou banco bloqueado.")
            conn.close()

    # DEBUG: Mostra quem está no banco para você conferir
    with st.expander("Ver lista de usuários no arquivo"):
        conn = sqlite3.connect(DB_PATH)
        users = conn.execute("SELECT username FROM users").fetchall()
        st.write(users)
        conn.close()

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.title("Menu")
        if st.sidebar.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()
        st.write("Logado com sucesso!")

if __name__ == "__main__":
    main()
