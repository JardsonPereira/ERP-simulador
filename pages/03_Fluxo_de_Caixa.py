import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o caminho das utilidades
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 2. Conversão segura: converte data para string e depois para datetime sem fuso horário
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # 3. FILTRO RÍGIDO: Removemos tudo que não for Entrada ou Saída
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    # 4. Cálculo de sinal
    df['valor_efetivo'] = df.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)

    # 5. Interface e Filtros
    c1, c2 = st.columns(2)
    # Garante que as datas de filtro também sejam puras (sem fuso)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date() if not df.empty else pd.Timestamp.now().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date() if not df.empty else pd.Timestamp.now().date())
    
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask].copy()

    # 6. Cálculos Financeiros
    saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    total_entradas = df_fc[df_fc['status_limpo'] == 'Entrada']['valor'].sum()
    total_saidas = df_fc[df_fc['status_limpo'] == 'Saída']['valor'].sum()
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 7. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']].sort_values('data_lancamento', ascending=False), use_container_width=True)

else:
    st.info("Nenhum lançamento de Entrada/Saída encontrado.")
