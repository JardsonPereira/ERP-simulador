import streamlit as st, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

check_auth(); inject_css()
st.header("💵 Fluxo de Caixa Detalhado")
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    
    df_anterior = df[df['data_lancamento'].dt.date < d_inicio].copy()
    df_anterior['fluxo_ant'] = df_anterior.apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else (-x['valor'] if x['status_financeiro'] == 'PAGO' else 0), axis=1)
    saldo_inicial = df_anterior['fluxo_ant'].sum()
    df_fc = df.loc[mask_periodo & df['status_financeiro'].isin(['ENTRADA', 'PAGO'])].copy()
    df_fc['fluxo'] = df_fc.apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else -x['valor'], axis=1)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {df_fc[df_fc['fluxo'] > 0]['fluxo'].sum():,.2f}")
    col3.metric("Saídas", f"R$ {abs(df_fc[df_fc['fluxo'] < 0]['fluxo'].sum()):,.2f}")
    col4.metric("Saldo Final", f"R$ {(saldo_inicial + df_fc['fluxo'].sum()):,.2f}")
    st.table(df_fc[['data_lancamento', 'nome_conta', 'operacao', 'valor', 'status_financeiro']])
    
    if st.download_button("Baixar Fluxo de Caixa PDF", data=gerar_relatorio_pdf("Fluxo de Caixa", df_fc), file_name="fluxo.pdf"): st.success("Download iniciado!")
