import streamlit as st
# Importando todas as funções do utils que criamos
from utils import (
    get_supabase, 
    inject_css, 
    get_data_cached, 
    resetar_lancamentos, 
    deletar_lancamento_por_id, 
    check_auth
)

# 1. Configuração da página
st.set_page_config(page_title="ERP Simulador", layout="wide")

# 2. Injeta o CSS (agora sem erros, o código verifica se o arquivo existe)
inject_css("style.css")

# --- SUA INTERFACE COMEÇA AQUI ---

def main():
    st.title("🔐 Login / Cadastro")

    # Exemplo de onde ficaria seu formulário
    # email = st.text_input("Email")
    # password = st.text_input("Senha", type="password")
    
    # if st.button("Entrar"):
    #     # Lógica de autenticação com Supabase
    #     pass

    # Exemplo de verificação de autenticação (Descomente se já estiver logado)
    # check_auth()

    # Se precisar buscar dados:
    if "user" in st.session_state:
        st.write(f"Olá, {st.session_state['user']['email']}")
        # dados = get_data_cached("lancamentos", st.session_state["user"]["id"])
        # st.write(dados)

if __name__ == "__main__":
    main()

# --- SUA INTERFACE TERMINA AQUI ---
