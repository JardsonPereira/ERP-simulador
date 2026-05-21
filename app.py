import streamlit as st
from supabase import create_client
import pandas as pd

# Configuração Supabase
SUPABASE_URL = "SUA_URL_AQUI"
SUPABASE_KEY = "SUA_KEY_AQUI"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(layout="wide")

# Autenticação Simples
if 'user' not in st.session_state:
    st.title("Login / Cadastro")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    username = st.text_input("Nome de Usuário")
    
    col1, col2 = st.columns(2)
    if col1.button("Cadastrar"):
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute()
            st.success("Conta criada! Faça login.")
            
    if col2.button("Entrar"):
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state.user = res.user
            st.rerun()
    st.stop()

# --- ÁREA LOGADA ---
st.sidebar.title(f"Bem-vindo!")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Estoque", "DRE"])

# Função auxiliar de leitura
def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- Lógica de Lançamento ---
if menu == "Lançamentos":
    st.header("Novo Lançamento")
    contas = get_data("contas")
    conta_escolhida = st.selectbox("Conta", [c['nome_conta'] for c in contas])
    valor = st.number_input("Valor", min_value=0.0)
    op = st.selectbox("Operação", ["DEBITO", "CREDITO"])
    
    if st.button("Salvar"):
        # Encontre o ID da conta e insira na tabela lancamentos
        st.success("Lançamento salvo!")

# --- Lógica Contabilidade (Razonetes) ---
elif menu == "Contabilidade":
    st.header("Razonetes e Balancete")
    lancamentos = get_data("lancamentos")
    df = pd.DataFrame(lancamentos)
    st.dataframe(df)
    
    # Exemplo simples de soma por grupo
    if not df.empty:
        balancete = df.groupby(['conta_id', 'operacao'])['valor'].sum().unstack().fillna(0)
        st.write("Balancete Simplificado:", balancete)

# --- Lógica DRE ---
elif menu == "DRE":
    st.header("Demonstração do Resultado")
    # Aqui você filtraria contas de receita - despesas
    st.write("Receitas: R$ 0.00")
    st.write("(-) CMV: R$ 0.00")
    st.write("= Lucro Líquido: R$ 0.00")
