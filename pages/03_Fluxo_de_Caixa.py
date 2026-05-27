import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# Carrega as variáveis do seu arquivo .env
load_dotenv()

# Conexão
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

# Configuração da página
st.set_page_config(page_title="Fluxo de Caixa", layout="wide")
check_auth()
inject_css()

st.title("📊 Fluxo de Caixa")

# 1. Carregamento
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    # Merge dos dados
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
    
    # Processamento
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    # 2. Sidebar (Filtros e PDF)
    with st.sidebar:
        st.header("⚙️ Filtros")
        contas_disponiveis = df['nome_conta'].unique()
        contas_selecionadas = st.multiselect("Filtrar Contas:", contas_disponiveis, default=contas_disponiveis)
        d_inicio = st.date_input("Início", value=df['data_lancamento'].min())
        d_fim = st.date_input("Fim", value=df['data_lancamento'].max())
        
        st.markdown("---")
        mask_pdf = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim) & (df['nome_conta'].isin(contas_selecionadas))
        pdf_bytes = gerar_relatorio_pdf("Fluxo de Caixa", df[mask_pdf])
        st.download_button("📥 Baixar Relatório PDF", data=pdf_bytes, file_name="fluxo_caixa.pdf")

    # Aplicação dos filtros
    mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim) & (df['nome_conta'].isin(contas_selecionadas))
    df_periodo = df[mask].copy()

    # 3. Abas
    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "💧 Liquidez e Passivos", "📋 Detalhes"])

    with tab1:
        total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {total_entradas:,.2f}")
        c2.metric("Total Saídas", f"R$ {total_saidas:,.2f}")
        c3.metric("Saldo", f"R$ {total_entradas - total_saidas:,.2f}")
        
        df_periodo['valor_efetivo'] = df_periodo.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)
        st.line_chart(df_periodo.groupby('data_lancamento')['valor_efetivo'].sum().cumsum())

    with tab2:
        st.subheader("Análise de Liquidez (Entradas vs. Passivos)")
        
        # Lógica Natural: Entradas = Disponibilidade (Ativo), Saídas = Passivo
        entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        passivos = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        
        liquidez = (entradas / passivos) if passivos > 0 else (entradas if entradas > 0 else 0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Disponível (Ativos)", f"R$ {entradas:,.2f}")
        c2.metric("Total Passivos (Saídas)", f"R$ {passivos:,.2f}")
        c3.metric("Índice de Liquidez", f"{liquidez:,.2f}")
        
        st.info("O índice de liquidez mostra quanto você tem de entradas para cobrir cada R$ 1,00 de passivos (saídas) no período.")

    with tab3:
        st.dataframe(df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum dado para exibir.")
