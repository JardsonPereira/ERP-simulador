import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, check_auth

check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira")

tab_visualizar, tab_lancamento, tab_contas = st.tabs(["📊 Lançamentos", "➕ Novo Lançamento", "🏦 Gerenciar Contas"])

# --- Aba de Visualização ---
with tab_visualizar:
    st.header("Lançamentos Realizados")
    # (Seu código original de exibição do dataframe vai aqui)
    # DICA: Adicione um botão de 'Atualizar' usando st.cache_data.clear()

# --- Aba de Novo Lançamento ---
with tab_lancamento:
    st.header("Registrar Movimentação")
    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data")
            conta = st.selectbox("Conta", options=get_data_cached("contas", st.session_state.user.id))
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        with col2:
            tipo = st.radio("Operação", ["Receita", "Despesa"])
            justificativa = st.text_area("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            # Lógica para inserir no Supabase
            # supabase.table("lancamentos").insert({...}).execute()
            st.success("Lançamento salvo!")

# --- Aba de Contas ---
with tab_contas:
    st.header("Minhas Contas")
    nome_nova_conta = st.text_input("Nome da nova conta")
    if st.button("Criar Conta"):
        # Lógica para inserir no Supabase
        st.success(f"Conta {nome_nova_conta} criada!")
