import streamlit as st
import pandas as pd
import sys
import os

# Caminho para utils
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
    
    # 2. Normalização e conversão
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento']).dt.date
    
    # Lógica de sinal (Entrada=1, Saída=-1, outros=0)
    def converter_status_para_sinal(status):
        s = str(status).strip().capitalize()
        if s == 'Entrada': return 1
        elif s == 'Saída': return -1
        return 0

    df['sinal'] = df['status_financeiro'].apply(converter_status_para_sinal)
    df['valor_efetivo'] = df['valor'] * df['sinal']

    # 3. Filtros de Período
    c1, c2 = st.columns(2)
    # Define valores padrão para não travar
    data_min = df['data_lancamento'].min()
    data_max = df['data_lancamento'].max()
    
    d_inicio = c1.date_input("Início", value=data_min)
    d_fim = c2.date_input("Fim", value=data_max)
    
    # --- CORREÇÃO: Filtro aplicado corretamente ---
    mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim)
    df_fc = df[mask].copy()

    # 4. Cálculos baseados APENAS no período filtrado (df_fc)
    # Saldo Inicial: tudo o que veio antes do d_inicio
    saldo_inicial = df[df['data_lancamento'] < d_inicio]['valor_efetivo'].sum()
    
    # Totais do período filtrado
    entradas = df_fc[df_fc['sinal'] == 1]['valor'].sum()
    saidas = df_fc[df_fc['sinal'] == -1]['valor'].sum()
    
    # Saldo final = Saldo inicial + movimentações do período (df_fc)
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 5. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {entradas:,.2f}")
    col3.metric("Saídas", f"R$ {saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.subheader("Lançamentos do Período")
    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento encontrado.")
