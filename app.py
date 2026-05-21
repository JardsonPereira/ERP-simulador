import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Didático 2026", layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LÓGICA DE NEGÓCIO ---
def registrar_lancamento(user_id, desc, nat, tipo, valor, justificativa, status, data):
    payload = {
        "user_id": user_id, "descricao": desc, "natureza": nat, "tipo": tipo,
        "valor": valor, "justificativa": justificativa, "status": status,
        "data_lancamento": str(data)
    }
    supabase.table("lancamentos").insert(payload).execute()

# --- TELAS ---
def mostrar_vendas_e_pagamentos(user_id):
    st.header("🛒 Módulo de Entradas e Saídas")
    col1, col2 = st.columns(2)
    
    with col1: # ENTRADAS
        st.subheader("📥 Entrada")
        with st.form("entrada"):
            desc = st.text_input("Descrição")
            nat = st.selectbox("Grupo", ["Ativo Circulante", "Patrimônio Líquido", "Receitas", "Investimentos"])
            tipo = st.radio("Operação", ["Débito", "Crédito"], key="in_tipo")
            valor = st.number_input("Valor", min_value=0.0, key="in_valor")
            status = st.selectbox("Status", ["Entrada", "Pendente", "Investimento", "Transação Interna"])
            data = st.date_input("Data", key="in_data")
            just = st.text_area("Justificativa")
            if st.form_submit_button("Confirmar Entrada"):
                registrar_lancamento(user_id, desc, nat, tipo, valor, just, status, data)
                st.success("Entrada registrada!")

    with col2: # SAÍDAS
        st.subheader("📤 Saída")
        with st.form("saida"):
            desc = st.text_input("Descrição", key="out_desc")
            nat = st.selectbox("Grupo", ["Passivo Circulante", "CMV", "Despesas", "Encargos Financeiros"])
            tipo = st.radio("Operação", ["Débito", "Crédito"], key="out_tipo")
            valor = st.number_input("Valor", min_value=0.0, key="out_valor")
            status = st.selectbox("Status", ["Pago", "Pendente"], key="out_status")
            data = st.date_input("Data", key="out_data")
            just = st.text_area("Justificativa", key="out_just")
            if st.form_submit_button("Confirmar Saída"):
                registrar_lancamento(user_id, desc, nat, tipo, valor, just, status, data)
                st.success("Saída registrada!")

def mostrar_contabilidade(user_id):
    st.header("📊 Contabilidade e Fluxo")
    data = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute().data
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)
        
        # Fluxo de Caixa (Apenas Entradas e Pagos)
        fluxo = df[df['status'].isin(['Entrada', 'Pago'])]
        soma = fluxo['valor'].sum()
        st.metric("Saldo do Fluxo de Caixa (Disponibilidades)", f"R$ {soma:,.2f}")
    else:
        st.info("Nenhum lançamento encontrado.")

# --- NAVEGAÇÃO E LOGIN ---
if not st.session_state.user:
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("E-mail")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except:
            st.sidebar.error("Erro no login.")
else:
    menu = st.sidebar.radio("Navegação", ["🛒 Vendas/Pagamentos", "📊 Contabilidade"])
    if menu == "🛒 Vendas/Pagamentos":
        mostrar_vendas_e_pagamentos(st.session_state.user.id)
    elif menu == "📊 Contabilidade":
        mostrar_contabilidade(st.session_state.user.id)
