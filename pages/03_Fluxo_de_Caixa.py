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
    
    # 2. Conversão segura de valores
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])

    # 3. Lógica Robusta de Identificação (O coração da solução)
    def classificar_e_sinalizar(status):
        s = str(status).strip().lower()
        # Se contiver 'entrada' (ou variações), é positivo
        if 'entrada' in s:
            return 1
        # Se contiver 'saida' ou 'saida' (tratando o 'ã' como 'a'), é negativo
        elif 'saida' in s or 'saída' in s:
            return -1
        return 0

    df['sinal'] = df['status_financeiro'].apply(classificar_e_sinalizar)
    df['valor_efetivo'] = df['valor'] * df['sinal']

    # --- DEBUG: Verificação ---
    # Isso vai listar na tela o que o código identificou como Entrada/Saída
    with st.expander("🔍 Diagnóstico de Status (Clique para ver)"):
        st.write(df[['status_financeiro', 'valor', 'sinal', 'valor_efetivo']].head(10))

    # 4. Interface e Filtros
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask].copy()

    # 5. Cálculos
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio)]['valor_efetivo'].sum()
    
    # Soma de entradas (onde sinal == 1) e saídas (onde sinal == -1)
    # Importante: usamos valor absoluto na exibição para não mostrar número negativo
    total_entradas = df_fc[df_fc['sinal'] == 1]['valor'].sum()
    total_saidas = df_fc[df_fc['sinal'] == -1]['valor'].sum()
    
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 6. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento encontrado.")
