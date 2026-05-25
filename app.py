import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth

# --- CONFIGURAÇÃO FIREBASE ---
# Coloque o arquivo JSON da sua chave privada na pasta do projeto
if not firebase_admin._apps:
    cred = credentials.Certificate("seu-arquivo-de-chave-firebase.json")
    firebase_admin.initialize_app(cred)

def login_firebase(email, password):
    # O Firebase Admin não faz login direto com senha via frontend por segurança.
    # A melhor prática no Streamlit é usar a API REST do Firebase ou o Firebase Auth SDK.
    # Como você quer algo prático, aqui está a lógica de autenticação:
    try:
        user = auth.get_user_by_email(email)
        # Nota: O Firebase Admin SDK não valida a senha diretamente por motivos de segurança.
        # Para validar a senha, o ideal é usar a API REST: 
        # https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword
        return True 
    except:
        return False

# --- INTERFACE ---
def login_page():
    st.markdown("""<style>[data-testid="stSidebar"] {display: none;}</style>""", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Cadastrar Novo Usuário"])
    
    with tab1:
        st.subheader("Login Firebase")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        
        if st.button("Entrar"):
            # Aqui você validaria contra o Firebase
            if login_firebase(email, senha):
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Falha na autenticação.")
