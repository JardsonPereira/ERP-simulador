import streamlit as st
import pandas as pd
import sys
import os

# Caminho para utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.set_page_config(page_title="Fluxo de Caixa", layout="wide")

st.title("📊 Fluxo de Caixa Dinâmico")

# 1. Carregamento e Preparação
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
    
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()
    df['valor_efetivo'] = df.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)

    # 2. FILTROS DINÂMICOS NA LATERAL
    with st.sidebar:
        st.header("⚙️ Filtros")
        contas_disponiveis = df['nome_conta'].unique()
        contas_selecionadas = st.multiselect("Filtrar Contas:", contas_disponiveis, default=contas_disponiveis)
        
        d_inicio = st.date_input("Início", value=df['data_lancamento'].min())
        d_fim = st.date_input("Fim", value=df['data_lancamento'].max())

    # Aplicar filtros
    mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim) & (df['nome_conta'].isin(contas_selecionadas))
    df_periodo = df[mask].copy()

    # 3. ABAS DE VISUALIZAÇÃO
    tab1, tab2 = st.tabs(["📈 Visão Geral", "📋 Detalhes"])

    with tab1:
        # Cálculos
        total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        saldo_final = total_entradas - total_saidas

        # Métricas com visual aprimorado
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {total_entradas:,.2f}")
        c2.metric("Total Saídas", f"R$ {total_saidas:,.2f}")
        c3.metric("Saldo do Período", f"R$ {saldo_final:,.2f}", delta=f"{saldo_final:,.2f}")

        st.markdown("### Evolução Diária")
        # Gráfico dinâmico
        chart_data = df_periodo.groupby('data_lancamento')['valor_efetivo'].sum().cumsum().reset_index()
        st.line_chart(chart_data.set_index('data_lancamento'))

    with tab2:
        st.subheader("Lançamentos Detalhados")
        # Tabela interativa com formatação
        st.dataframe(
            df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']]
            .sort_values('data_lancamento', ascending=False),
            use_container_width=True,
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "data_lancamento": st.column_config.DateColumn("Data")
            }
        )

else:
    st.warning("Nenhum dado encontrado.")
