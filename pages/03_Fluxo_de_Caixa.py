import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa e Indicadores")

user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Garantir que temos a coluna 'grupo' (Corrigindo o problema de nomeação do merge)
    df['grupo'] = df.get('grupo_lanc', df.get('grupo_conta', 'Outros'))
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

    # --- CÁLCULOS DE LIQUIDEZ E PASSIVOS (Baseado no saldo total de todas as datas) ---
    ativo_circ = df[df['grupo'] == 'Ativo Circulante']['valor'].sum()
    passivo_circ = df[df['grupo'] == 'Passivo Circulante']['valor'].sum()
    passivo_nao_circ = df[df['grupo'] == 'Passivo Não Circulante']['valor'].sum()
    
    liquidez_corrente = (ativo_circ / passivo_circ) if passivo_circ > 0 else 0
    total_passivos = passivo_circ + passivo_nao_circ

    # --- INDICADORES FINANCEIROS (Linha 1) ---
    st.subheader("Indicadores de Saúde Financeira")
    colA, colB, colC = st.columns(3)
    colA.metric("Liquidez Corrente", f"{liquidez_corrente:.2f}")
    colB.metric("Passivo Circulante", f"R$ {passivo_circ:,.2f}")
    colC.metric("Passivo Não Circulante", f"R$ {passivo_nao_circ:,.2f}")

    # --- FLUXO DE CAIXA (Sua lógica anterior) ---
    st.markdown("---")
    st.subheader("Fluxo de Caixa")
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    df['valor_efetivo'] = df.apply(lambda x: x['valor'] if x['status_financeiro'] == 'Entrada' else (-x['valor'] if x['status_financeiro'] == 'Saída' else 0), axis=1)
    
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    mask_valido = df['status_financeiro'].isin(['Entrada', 'Saída'])
    df_fc = df[mask_periodo & mask_valido].copy()
    
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio) & mask_valido]['valor_efetivo'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum():,.2f}")
    col3.metric("Saídas", f"R$ {df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum():,.2f}")
    col4.metric("Saldo Final", f"R$ {(saldo_inicial + df_fc['valor_efetivo'].sum()):,.2f}")
    
    st.dataframe(df_fc[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento encontrado.")
