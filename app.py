import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv

# Configuração
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="ERP Didático", layout="wide")

# --- AUTENTICAÇÃO ---
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
            st.success("Conta criada!")
            
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error("Erro no login.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Estoque", "DRE"])

def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- ABA LANÇAMENTOS E CONTAS ---
if menu == "Lançamentos":
    st.header("Gestão de Contas e Lançamentos")
    tab1, tab2 = st.tabs(["Lançar", "Criar Conta"])
    
    with tab2:
        st.subheader("Cadastro de Conta com Classificação")
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo Contábil", [
            "ATIVO CIRCULANTE", "ATIVO NÃO CIRCULANTE", 
            "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", 
            "PL", "RECEITAS", "DESPESAS", "CMV"
        ])
        if st.button("Salvar Conta"):
            supabase.table("contas").insert({
                "user_id": st.session_state.user.id, 
                "nome_conta": nome, 
                "grupo": grupo
            }).execute()
            st.success("Conta salva!")

    with tab1:
        contas = get_data("contas")
        if contas:
            mapa = {c['nome_conta']: c['id'] for c in contas}
            conta = st.selectbox("Conta", list(mapa.keys()))
            valor = st.number_input("Valor", min_value=0.0)
            op = st.selectbox("Operação", ["DEBITO", "CREDITO"])
            data = st.date_input("Data")
            status = st.selectbox("Status", ["ENTRADA", "PAGO", "PENDENTE", "INVESTIMENTO", "TRANSAÇÃO INTERNA"])
            
            if st.button("Confirmar Lançamento"):
                supabase.table("lancamentos").insert({
                    "user_id": st.session_state.user.id, "conta_id": mapa[conta],
                    "operacao": op, "valor": valor, "status_financeiro": status, "data_lancamento": str(data)
                }).execute()
                st.success("Lançado!")

# --- ABA CONTABILIDADE (RAZONETES) ---
elif menu == "Contabilidade":
    st.header("Razonetes")
    lancamentos = get_data("lancamentos")
    if lancamentos:
        df = pd.DataFrame(lancamentos)
        st.dataframe(df)
