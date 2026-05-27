import streamlit as st
import pandas as pd
import sys
import os

# Caminho para utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("📊 Fluxo de Caixa (Fiel ao Lançamento)")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 2. A CORREÇÃO DE DATA ESTÁ AQUI:
    # Convertemos para string e pegamos apenas os primeiros 10 caracteres (YYYY-MM-DD).
    # Depois, convertemos para objeto 'date'. Isso bloqueia o fuso horário.
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # 3. FILTRO CONTÁBIL RÍGIDO: Apenas Entrada e Saída
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    if not df.empty:
        # Cálculo de sinal (Crédito/Débito)
        df['valor_efetivo'] = df.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)

        # 4. Interface de Período
        c1, c2 = st.columns(2)
        # O uso de .date() garante consistência absoluta com o date_input
        d_inicio = c1.date_input("Início do Período", value=df['data_lancamento'].min())
        d_fim = c2.date_input("Fim do Período", value=df['data_lancamento'].max())
        
        # Filtro de data estrito
        mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim)
        df_periodo = df[mask].copy()
        
        # 5. Cálculos (Fidelidade ao período)
        saldo_inicial = df[df['data_lancamento'] < d_inicio]['valor_efetivo'].sum()
        total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        saldo_final = saldo_inicial + df_periodo['valor_efetivo'].sum()

        # 6. Exibição
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
        col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
        col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
        col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

        st.markdown("---")
        st.subheader("Lançamentos do Período Selecionado")
        st.dataframe(
            df_periodo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']]
            .sort_values('data_lancamento', ascending=False), 
            use_container_width=True
        )
    else:
        st.info("Nenhum lançamento de Entrada ou Saída encontrado para este período.")
else:
    st.warning("Dados não carregados.")
