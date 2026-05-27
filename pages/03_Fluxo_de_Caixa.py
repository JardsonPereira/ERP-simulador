import streamlit as st
import pandas as pd
import sys
import os
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# Caminho para o diretório raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- CONFIGURAÇÃO DE MAPEAMENTO ---
# AQUI VOCÊ CLASSIFICA: Nome da Conta no Supabase : Categoria
MAPA_PASSIVOS = {
    "Fornecedores": "Circulante",
    "Cartão de Crédito": "Circulante",
    "Impostos": "Circulante",
    "Empréstimo": "Não Circulante",
    "Financiamento": "Não Circulante"
}

st.set_page_config(page_title="Fluxo de Caixa", layout="wide")
check_auth() 
inject_css()

st.title("📊 Fluxo de Caixa")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # Classificação automática baseada no MAPA_PASSIVOS
    df['tipo_passivo'] = df['nome_conta'].map(MAPA_PASSIVOS).fillna("Não Classificado")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Filtros")
        contas_disponiveis = df['nome_conta'].unique()
        contas_selecionadas = st.multiselect("Filtrar Contas:", contas_disponiveis, default=contas_disponiveis)
        d_inicio = st.date_input("Início", value=df['data_lancamento'].min())
        d_fim = st.date_input("Fim", value=df['data_lancamento'].max())

    # Filtros
    mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim) & (df['nome_conta'].isin(contas_selecionadas))
    df_periodo = df[mask].copy()

    # Abas
    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "💧 Liquidez e Passivos", "📋 Detalhes"])

    with tab1:
        entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        st.metric("Saldo Final", f"R$ {entradas - saidas:,.2f}")
        df_periodo['valor_efetivo'] = df_periodo.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)
        st.line_chart(df_periodo.groupby('data_lancamento')['valor_efetivo'].sum().cumsum())

    with tab2:
        st.subheader("Análise de Solvência")
        
        # Cálculos
        saldo_final = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum() - df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        
        df_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']
        p_circulante = df_saidas[df_saidas['tipo_passivo'] == 'Circulante']['valor'].sum()
        p_nao_circulante = df_saidas[df_saidas['tipo_passivo'] == 'Não Circulante']['valor'].sum()
        total_passivos = p_circulante + p_nao_circulante
        
        liquidez = (saldo_final / total_passivos) if total_passivos > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Final", f"R$ {saldo_final:,.2f}")
        c2.metric("Total Passivos", f"R$ {total_passivos:,.2f}")
        c3.metric("Índice de Solvência", f"{liquidez:,.2f}")
        
        # --- TABELA DE DADOS DOS PASSIVOS ---
        st.markdown("### Detalhamento dos Passivos (Lançamentos)")
        if total_passivos > 0:
            cols_exibir = ['data_lancamento', 'nome_conta', 'tipo_passivo', 'valor', 'justificativa']
            st.dataframe(df_saidas[cols_exibir], use_container_width=True)
        else:
            st.info("Nenhum passivo classificado no período.")

    with tab3:
        st.dataframe(df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor']], use_container_width=True)
else:
    st.info("Nenhum dado encontrado.")
