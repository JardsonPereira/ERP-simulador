import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # --- DIAGNÓSTICO (Remova se desejar) ---
    # Isso mostrará o que está na sua coluna Status. Se aparecer algo diferente 
    # de "Entrada" ou "Saída", você saberá exatamente o que ajustar abaixo.
    st.write("Valores encontrados no status:", df['status_financeiro'].unique())

    # --- LÓGICA DE FLEXIBILIZAÇÃO ---
    def definir_sinal(status):
        s = str(status).strip().lower()
        # Se contiver 'entrada', retorna 1 (soma), se 'saída' ou 'saida', retorna -1 (subtrai)
        if 'entrada' in s:
            return 1
        elif 'saida' in s or 'saída' in s:
            return -1
        return 0

    df['multiplicador'] = df['status_financeiro'].apply(definir_sinal)
    df['valor_efetivo'] = df['valor'] * df['multiplicador']

    # --- FLUXO DE CAIXA ---
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask_periodo].copy()
    
    # Cálculos
    # Saldo Inicial: tudo que aconteceu antes da d_inicio que seja entrada/saída (multiplicador != 0)
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio) & (df['multiplicador'] != 0)]['valor_efetivo'].sum()
    
    # Totais
    total_entradas = df_fc[df_fc['multiplicador'] == 1]['valor'].sum()
    total_saidas = df_fc[df_fc['multiplicador'] == -1]['valor'].sum()
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento encontrado.")
