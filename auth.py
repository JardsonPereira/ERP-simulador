import streamlit as st

def login_form():
    st.title("Login")
    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        # Adicione aqui a lógica de validação no seu banco de dados
        if username == "admin" and password == "123":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

    if st.button("Criar Nova Conta"):
        st.session_state.page = "register"
        st.rerun()

def register_form():
    st.title("Cadastro")
    new_user = st.text_input("Novo Usuário")
    new_pass = st.text_input("Nova Senha", type="password")
    
    if st.button("Cadastrar"):
        # Lógica para salvar no banco de dados
        st.success("Conta criada! Faça o login.")
        st.session_state.page = "login"
        st.rerun()
