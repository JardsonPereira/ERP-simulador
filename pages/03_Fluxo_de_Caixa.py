import streamlit as st
import pandas as pd
import sys
import os
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# Configuração da Página
st.set_page_config(page_title="Fluxo de Caixa", layout="wide")
check_auth()
inject_css()

# --- CONFIGURAÇÃO DE MAPEAMENTO (Onde você define o que é Circulante ou Não) ---
# Adicione aqui o nome das suas contas exatamente como estão no seu Supabase
MAPA_PASSIVOS = {
    "Fornecedores": "Circulante",
    "Cartão de Crédito": "Circulante",
    "Impostos": "Circulante",
    "Empréstimos Bancários": "Não Circulante",
    "Financiamentos": "Não Circulante"
}

st.title("📊 Fluxo de Caixa")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    # Merge
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
    
    # Processamento padrão
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # --- Classificação Automática dos Passivos ---
    # Se a conta não estiver no mapa, assume-se "Outros"
    df['tipo_passivo'] = df['nome_conta'].map(MAPA_PASSIVOS).fillna("Outros")

    # 2. Sidebar (Filtros)
    with st.sidebar:
        st.header("⚙️ Filtros")
        d_inicio = st.date_input("Início", value=df['data_lancamento'].min())
        d_fim = st.date_input("Fim", value=df['data_lancamento'].max())

    # Aplicação dos filtros
    mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim)
    df_periodo = df[mask].copy()

    # 3. Abas
    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "💧 Liquidez e Passivos", "📋 Detalhes"])

    with tab1:
        entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:,.2f}")
        c2.metric("Total Saídas", f"R$ {saidas:,.2f}")
        c3.metric("Saldo", f"R$ {entradas - saidas:,.2f}")

    with tab2:
        st.subheader("Análise Detalhada de Passivos")
        
        # Filtra apenas saídas para analisar os passivos
        df_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']
        
        circulante = df_saidas[df_saidas['tipo_passivo'] == 'Circulante']['valor'].sum()
        nao_circulante = df_saidas[df_saidas['tipo_passivo'] == 'Não Circulante']['valor'].sum()
        ativo_disponivel = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        
        # Métricas de Passivos
        c1, c2, c3 = st.columns(3)
        c1.metric("Passivo Circulante", f"R$ {circulante:,.2f}")
        c2.metric("Passivo Não Circulante", f"R$ {nao_circulante:,.2f}")
        c3.metric("Ativo Disponível", f"R$ {ativo_disponivel:,.2f}")
        
        st.markdown("---")
        # Liquidez Corrente (Ativo / Passivo Circulante)
        liquidez_corrente = (ativo_disponivel / circulante) if circulante > 0 else 0
        st.metric("Índice de Liquidez Corrente", f"{liquidez_corrente:,.2f}")
        
        st.info("O Índice de Liquidez Corrente mede sua capacidade de pagar dívidas de curto prazo (Circulante) com suas entradas disponíveis.")

    with tab3:
        st.dataframe(df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'tipo_passivo', 'valor']], use_container_width=True)

else:
    st.info("Nenhum dado encontrado.")
