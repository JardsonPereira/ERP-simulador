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
    
    # 2. Limpeza e conversão numérica
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # 3. Lógica de Reflexão no Fluxo (Sinal)
    # Entrada = 1, Saída = -1, Outros = 0 (Ignora Transação Interna, Pendente, etc)
    def definir_sinal(status):
        s = str(status).strip()
        if s == 'Entrada':
            return 1
        elif s == 'Saída':
            return -1
        else:
            return 0 # Não afeta o caixa

    df['sinal'] = df['status_financeiro'].apply(definir_sinal)
    df['valor_efetivo'] = df['valor'] * df['sinal']

    # --- DEBUG PARA VOCÊ VER O QUE ESTÁ ACONTECENDO ---
    with st.expander("🔍 Diagnóstico do Fluxo"):
        st.write(df[['status_financeiro', 'valor', 'sinal', 'valor_efetivo']])

    # 4. Filtros
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask].copy()

    # 5. Cálculos usando o sinal (Soma negativa subtrai do total)
    saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    
    # Exibe apenas os valores positivos de entrada e saída para as métricas
    total_entradas = df_fc[df_fc['sinal'] == 1]['valor'].sum()
    total_saidas = df_fc[df_fc['sinal'] == -1]['valor'].sum()
    
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 6. Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']])

else:
    st.info("Nenhum lançamento encontrado.")
