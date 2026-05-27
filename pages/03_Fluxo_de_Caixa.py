import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o caminho das utilidades se necessário
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

# Configurações iniciais
check_auth()
inject_css()

st.header("💵 Fluxo de Caixa e Indicadores")

# Carregar dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    # Preparação do DataFrame
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Normalização de colunas
    df['grupo'] = df.get('grupo_lanc', df.get('grupo_conta', 'Outros'))
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_financeiro'] = df['status_financeiro'].astype(str).str.capitalize().str.strip()

    # --- INDICADORES FINANCEIROS (Estáticos) ---
    st.subheader("Indicadores de Saúde Financeira")
    
    # Cálculos de liquidez
    ativo_circ = df[df['grupo'] == 'Ativo Circulante']['valor'].sum()
    passivo_circ = df[df['grupo'] == 'Passivo Circulante']['valor'].sum()
    passivo_nao_circ = df[df['grupo'] == 'Passivo Não Circulante']['valor'].sum()
    
    liquidez_corrente = (ativo_circ / passivo_circ) if passivo_circ > 0 else 0

    colA, colB, colC = st.columns(3)
    colA.metric("Liquidez Corrente", f"{liquidez_corrente:.2f}")
    colB.metric("Passivo Circulante", f"R$ {passivo_circ:,.2f}")
    colC.metric("Passivo Não Circulante", f"R$ {passivo_nao_circ:,.2f}")

    # --- FLUXO DE CAIXA (Dinâmico) ---
    st.markdown("---")
    st.subheader("Fluxo de Caixa")
    
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    # Criar coluna de valor efetivo (Entradas positivas, Saídas negativas)
    def aplicar_valor(row):
        if row['status_financeiro'] == 'Entrada':
            return row['valor']
        elif row['status_financeiro'] == 'Saída':
            return -row['valor']
        return 0

    df['valor_efetivo'] = df.apply(aplicar_valor, axis=1)

    # Filtragem de período
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    mask_valido = df['status_financeiro'].isin(['Entrada', 'Saída'])
    
    # Dados para exibição no período
    df_fc = df[mask_periodo & mask_valido].copy()
    
    # Cálculo do saldo inicial (Tudo o que aconteceu antes da data início)
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio) & mask_valido]['valor_efetivo'].sum()
    
    # Cálculos para métricas do período
    total_entradas = df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum()
    total_saidas = df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum()
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")
    
    # Tabela de detalhamento
    st.dataframe(
        df_fc[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']]
        .sort_values('data_lancamento'), 
        use_container_width=True
    )

else:
    st.info("Nenhum lançamento encontrado para exibir o Fluxo de Caixa.")
