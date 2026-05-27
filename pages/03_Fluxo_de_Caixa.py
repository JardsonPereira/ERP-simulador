import streamlit as st
import pandas as pd
import sys
import os

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
    
    # 2. Normalização de dados (Limpeza profunda)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Função que define o comportamento de cada status
    def converter_status_para_sinal(status):
        s = str(status).strip().capitalize() # Remove espaços e padroniza a primeira letra
        if s == 'Entrada':
            return 1   # Multiplicador positivo
        elif s == 'Saída':
            return -1  # Multiplicador negativo
        else:
            return 0   # Ignora Transação Interna, Pendente, etc.

    # 3. Aplicar a lógica de sinal
    df['sinal'] = df['status_financeiro'].apply(converter_status_para_sinal)
    df['valor_efetivo'] = df['valor'] * df['sinal']

    # 4. Filtro: Manter apenas o que afeta o caixa (sinal != 0)
    df_caixa = df[df['sinal'] != 0].copy()

    # 5. Interface
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df_caixa['data_lancamento'].min().date() if not df_caixa.empty else pd.Timestamp.now().date())
    d_fim = c2.date_input("Fim", value=df_caixa['data_lancamento'].max().date() if not df_caixa.empty else pd.Timestamp.now().date())
    
    mask = (df_caixa['data_lancamento'].dt.date >= d_inicio) & (df_caixa['data_lancamento'].dt.date <= d_fim)
    df_fc = df_caixa[mask].copy()

    # 6. Cálculos
    saldo_inicial = df_caixa[df_caixa['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    
    entradas = df_fc[df_fc['sinal'] == 1]['valor'].sum()
    saidas = df_fc[df_fc['sinal'] == -1]['valor'].sum()
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 7. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {entradas:,.2f}")
    col3.metric("Saídas", f"R$ {saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento de Entrada/Saída encontrado.")
