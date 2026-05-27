import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime

# Ajuste seguro de caminho para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from utils import get_data_cached, check_auth, inject_css
except ImportError:
    st.error("Erro: O arquivo 'utils.py' não foi encontrado na raiz do projeto. Verifique a estrutura de pastas.")
    st.stop()

check_auth()
inject_css()

st.header("📊 Fluxo de Caixa (Contábil)")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df_l = pd.DataFrame(lancamentos)
    df_c = pd.DataFrame(contas)
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # 2. TRATAMENTO RÍGIDO DE DADOS
    # Converte data ignorando fuso horário e força o formato date
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # 3. FILTRO CONTÁBIL: Apenas Entrada e Saída
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    if not df.empty:
        # 4. Cálculo do valor efetivo (Sinal contábil)
        df['valor_efetivo'] = df.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)

        # 5. Interface de Período com proteção contra DataFrame vazio
        c1, c2 = st.columns(2)
        min_date = df['data_lancamento'].min()
        max_date = df['data_lancamento'].max()
        
        d_inicio = c1.date_input("Início do Período", value=min_date)
        d_fim = c2.date_input("Fim do Período", value=max_date)
        
        # Filtro de período
        mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim)
        df_periodo = df[mask].copy()
        
        # 6. Cálculos contábeis
        saldo_inicial = df[df['data_lancamento'] < d_inicio]['valor_efetivo'].sum()
        total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        saldo_final = saldo_inicial + df_periodo['valor_efetivo'].sum()

        # 7. Exibição
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
        col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
        col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
        col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

        st.markdown("---")
        st.dataframe(df_periodo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']].sort_values('data_lancamento', ascending=False), use_container_width=True)
    else:
        st.info("Nenhum lançamento de Entrada ou Saída encontrado para o período.")
else:
    st.warning("Não há lançamentos ou contas registradas para exibir.")
