import streamlit as st
import pandas as pd
import sys
import os

# Ajuste de caminho para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

# 1. Carregamento de Dados (Inicialize ANTES do IF)
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

# 2. Validação: Verifique se os dados existem e não estão vazios
if lancamentos and contas:
    df_l = pd.DataFrame(lancamentos)
    df_c = pd.DataFrame(contas)
    
    # Merge
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # 3. Limpeza e Padronização
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Padronização de status (limpa espaços e capitaliza)
    df['status_financeiro'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # --- FILTRO RÍGIDO: Apenas Entrada/Saída ---
    df = df[df['status_financeiro'].isin(['Entrada', 'Saída'])].copy()

    if not df.empty:
        # Função de cálculo
        def calcular_efetivo(row):
            val = float(row['valor'])
            # Se for Entrada, mantém positivo. Se Saída, negativo.
            return val if row['status_financeiro'] == 'Entrada' else -abs(val)

        df['valor_efetivo'] = df.apply(calcular_efetivo, axis=1)

        # 4. Interface do Fluxo
        c1, c2 = st.columns(2)
        
        # Proteção contra DataFrame vazio para o date_input
        data_min = df['data_lancamento'].min().date()
        data_max = df['data_lancamento'].max().date()
        
        d_inicio = c1.date_input("Início", value=data_min)
        d_fim = c2.date_input("Fim", value=data_max)
        
        # Filtros
        mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
        df_fc = df[mask].copy()
        
        # Cálculos
        saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
        entradas = df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum()
        saidas = df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum()
        saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

        # 5. Exibição
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
        col2.metric("Entradas", f"R$ {entradas:,.2f}")
        col3.metric("Saídas", f"R$ {saidas:,.2f}")
        col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

        st.markdown("---")
        st.subheader("Detalhamento")
        st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)
    else:
        st.info("Nenhum lançamento com status 'Entrada' ou 'Saída' encontrado.")
else:
    st.info("Nenhum dado de lançamentos ou contas encontrado.")
