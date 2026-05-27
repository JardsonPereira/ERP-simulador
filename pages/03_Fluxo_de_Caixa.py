import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("📊 Fluxo de Caixa (Contábil)")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 2. LIMPEZA RÍGIDA DE DATAS E VALORES
    # O uso de .str[:10] ignora horas e fusos, fixando a data exatamente como foi gravada
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Padronização de status
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # 3. FILTRO CONTÁBIL: Apenas Entrada e Saída
    # Qualquer outro status é ignorado pelo fluxo de caixa
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    # 4. Lógica de Sinal (Crédito/Débito)
    df['valor_efetivo'] = df.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)

    # 5. Interface de Período
    c1, c2 = st.columns(2)
    min_date = df['data_lancamento'].min().date() if not df.empty else pd.Timestamp.now().date()
    max_date = df['data_lancamento'].max().date() if not df.empty else pd.Timestamp.now().date()
    
    d_inicio = c1.date_input("Início do Período", value=min_date)
    d_fim = c2.date_input("Fim do Período", value=max_date)
    
    # 6. Cálculo fiel ao período selecionado
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_periodo = df[mask].copy()
    
    # Saldo Inicial: Tudo o que aconteceu antes do período
    saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    
    # Totais do período
    total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
    total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
    
    # Saldo Final
    saldo_final = saldo_inicial + df_periodo['valor_efetivo'].sum()

    # 7. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.dataframe(
        df_periodo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']]
        .sort_values('data_lancamento', ascending=False), 
        use_container_width=True
    )

else:
    st.info("Nenhum lançamento de Entrada ou Saída encontrado.")
