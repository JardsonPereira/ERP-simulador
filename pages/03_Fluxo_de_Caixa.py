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
    
    # --- DEBUG: ISSO VAI MOSTRAR O QUE O CÓDIGO ESTÁ LENDO ---
    # Se aparecer algo diferente de 'Entrada' ou 'Saída', já saberemos o motivo
    st.write("Status encontrados no banco:", df['status_financeiro'].unique())
    
    # --- PADRONIZAÇÃO AGRESSIVA ---
    # Remove espaços, coloca a primeira letra em maiúsculo
    df['status_financeiro'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()

    def calcular_efetivo(row):
        val = row['valor']
        # Compara de forma case-insensitive
        status = str(row['status_financeiro']).lower()
        
        if status == 'entrada':
            return val
        elif status == 'saída' or status == 'saida': # Aceita com ou sem acento
            return -abs(val)
        return 0

    df['valor_efetivo'] = df.apply(calcular_efetivo, axis=1)

    # --- FLUXO DE CAIXA ---
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask_periodo].copy()
    
    # Cálculo
    saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    entradas = df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum()
    saidas = df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum()
    
    # Saldo Final é a soma do inicial com as variações efetivas do período
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {entradas:,.2f}")
    col3.metric("Saídas", f"R$ {saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento encontrado.")
