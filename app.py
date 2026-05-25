import streamlit as st
from auth import login_form, register_form

# Inicializa o estado de login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "login"

def main():
    if not st.session_state.logged_in:
        if st.session_state.page == "login":
            login_form()
        elif st.session_state.page == "register":
            register_form()
    else:
        # Se estiver logado, exibe o menu principal
        st.sidebar.title("Menu Principal")
        st.write("Bem-vindo ao sistema!")
        if st.sidebar.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()
        # Aqui o Streamlit gerencia as páginas da pasta /pages automaticamente

if __name__ == "__main__":
    main()
