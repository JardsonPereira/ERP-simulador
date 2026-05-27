import streamlit as st, pandas as pd, sys, os
from datetime import date

# 1. Configurar o caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Importar as funções
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# 3. Executar configurações iniciais
check_auth()
inject_css()

st.header("💵 Fluxo de Caixa Detalhado")

# Carregar dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])

    # --- LÓGICA DE CÁLCULO DE FLUXO ---
    # Define o valor do fluxo: positivo para Entrada, negativo para Saída, 0 para outros
    df['fluxo_calculado'] = df.apply(
        lambda x: x['valor'] if x['status_financeiro'] == 'Entrada' 
        else (-x['valor'] if x['status_financeiro'] == 'Saída' else 0), 
        axis=1
    )

    # Filtros de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    
    # Saldo Inicial (Tudo antes da data de início com status Entrada/Saída)
    df_anterior = df[(df['data_lancamento'].dt.date < d_inicio) & (df['status_financeiro'].isin(['Entrada', 'Saída']))].copy()
    saldo_inicial = df_anterior['fluxo_calculado'].sum()
    
    # Fluxo do Período selecionado
    df_fc = df.loc[mask_periodo & df['status_financeiro'].isin(['Entrada', 'Saída'])].copy()
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum():,.2f}")
    col3.metric("Saídas", f"R$ {df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum():,.2f}")
    col4.metric("Saldo Final", f"R$ {(saldo_inicial + df_fc['fluxo_calculado'].sum()):,.2f}")
    
    # Tabela
    st.markdown("### Lançamentos no Período")
    st.dataframe(df_fc[['data_lancamento', 'nome_conta', 'operacao', 'valor', 'status_financeiro', 'justificativa']], use_container_width=True)
    
    # Botão de PDF
    if st.download_button("Baixar Fluxo de Caixa PDF", data=gerar_relatorio_pdf("Fluxo de Caixa", df_fc), file_name="fluxo.pdf"): 
        st.success("Download iniciado!")
else:
    st.info("Nenhum lançamento encontrado para exibir o fluxo de caixa.")
