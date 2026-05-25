import streamlit as st

# Configuração da página
st.set_page_config(page_title="Sistema Contabil", layout="wide")

# Inicialização do estado
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'users' not in st.session_state:
    # Lista inicial de usuários (pode ser carregada de um banco de dados no futuro)
    st.session_state.users = {"admin": "123"} 

def login_page():
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Cadastrar Novo Usuário"])
    
    with tab1:
        st.subheader("Login")
        user = st.text_input("Usuário")
        pw = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if st.session_state.users.get(user) == pw:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")
                
    with tab2:
        st.subheader("Novo Cadastro")
        new_user = st.text_input("Escolha um usuário")
        new_pw = st.text_input("Escolha uma senha", type="password")
        if st.button("Cadastrar"):
            if new_user in st.session_state.users:
                st.warning("Usuário já existe!")
            else:
                st.session_state.users[new_user] = new_pw
                st.success("Cadastro realizado com sucesso!")

    # Exibir lista de usuários cadastrados (conforme solicitado)
    with st.expander("Ver usuários já cadastrados"):
        for u in st.session_state.users.keys():
            st.write(f"- {u}")

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        st.sidebar.title("Menu Principal")
        st.write("Bem-vindo ao sistema!")
        if st.sidebar.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()

if __name__ == "__main__":
    main()
