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
    st.title("Login / Cadastro - ERP Didático")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    username = st.text_input("Nome de Usuário")
    
    col1, col2 = st.columns(2)
    if col1.button("Cadastrar"):
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute()
            st.success("Conta criada! Agora faça login.")
            
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error("Falha no login. Verifique suas credenciais.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.sidebar.title(f"Bem-vindo, {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Estoque", "DRE", "Fluxo de Caixa"])

def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- ABA LANÇAMENTOS ---
if menu == "Lançamentos":
    st.header("Lançamentos Contábeis")
    tab1, tab2 = st.tabs(["Realizar Lançamento", "Nova Conta"])
    
    with tab2:
        st.subheader("Cadastrar Nova Conta")
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO", "PASSIVO", "PL", "ENCARGOS FINANCEIROS", "DESPESAS", "RECEITAS", "CMV"])
        if st.button("Salvar Conta"):
            supabase.table("contas").insert({"user_id": st.session_state.user.id, "nome_conta": nome, "grupo": grupo}).execute()
            st.success("Conta salva!")
            st.rerun()

    with tab1:
        contas = get_data("contas")
        if not contas:
            st.warning("Crie uma conta primeiro na aba 'Nova Conta'.")
        else:
            mapa = {c['nome_conta']: c['id'] for c in contas}
            col_a, col_b = st.columns(2)
            with col_a:
                conta = st.selectbox("Conta", list(mapa.keys()))
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with col_b:
                op = st.selectbox("Operação", ["DEBITO", "CREDITO"])
                status = st.selectbox("Status", ["ENTRADA", "PAGO", "PENDENTE", "INVESTIMENTO", "TRANSAÇÃO INTERNA"])
                data = st.date_input("Data do Lançamento")
            
            if st.button("Confirmar Lançamento"):
                supabase.table("lancamentos").insert({
                    "user_id": st.session_state.user.id, 
                    "conta_id": mapa[conta],
                    "operacao": op, 
                    "valor": valor, 
                    "status_financeiro": status,
                    "data_lancamento": str(data)
                }).execute()
                st.success("Lançamento efetuado!")

# --- ABA CONTABILIDADE (RAZONETES/BALANCETE) ---
elif menu == "Contabilidade":
    st.header("Contabilidade: Razonetes e Balancete")
    lancamentos = get_data("lancamentos")
    if lancamentos:
        df = pd.DataFrame(lancamentos)
        st.dataframe(df)
        
        st.subheader("Balancete Simplificado")
        resumo = df.groupby(['conta_id', 'operacao'])['valor'].sum().unstack().fillna(0)
        resumo['Saldo'] = resumo.get('DEBITO', 0) - resumo.get('CREDITO', 0)
        st.table(resumo)

# --- OUTRAS ABAS (ESTRUTURA) ---
elif menu == "Estoque":
    st.header("Gestão de Estoque")
    st.info("Aqui você integrará as entradas e saídas com o custo das mercadorias.")

elif menu == "DRE":
    st.header("Demonstração do Resultado (DRE)")
    st.info("Relatório de Receitas vs Despesas.")

elif menu == "Fluxo de Caixa":
    st.header("Fluxo de Caixa")
    st.info("Acompanhamento das entradas e saídas de caixa.")
