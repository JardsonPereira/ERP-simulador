import streamlit as st
import pandas as pd
import sys
import os
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# Caminho para o diretório raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuração da Página
st.set_page_config(page_title="Fluxo de Caixa", layout="wide")
check_auth() 
inject_css()

st.title("📊 Fluxo de Caixa")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    # Merge dos dados
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
    
    # --- PROCESSAMENTO ROBUSTO ---
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Padroniza status (Entrada/Saída)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # Padroniza GRUPO para garantir que a busca funcione (Remove espaços e coloca tudo em minúsculo)
    if 'grupo' in df.columns:
        df['grupo_limpo'] = df['grupo'].astype(str).str.strip().str.lower()
    else:
        df['grupo_limpo'] = 'não definido'

    # Filtros da Sidebar
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
        entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {entradas:,.2f}")
        c2.metric("Total Saídas", f"R$ {saidas:,.2f}")
        c3.metric("Saldo Final", f"R$ {entradas - saidas:,.2f}")
        
        df_periodo['valor_efetivo'] = df_periodo.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)
        st.line_chart(df_periodo.groupby('data_lancamento')['valor_efetivo'].sum().cumsum())

    with tab2:
        st.subheader("Análise de Solvência (Saldo Final / Passivos)")
        
        # Filtros usando a versão limpa do grupo
        # Nota: usamos .str.lower() pois o grupo_limpo já está assim
        p_circulante = df_periodo[(df_periodo['status_limpo'] == 'Saída') & (df_periodo['grupo_limpo'] == 'circulante')]['valor'].sum()
        p_nao_circulante = df_periodo[(df_periodo['status_limpo'] == 'Saída') & (df_periodo['grupo_limpo'] == 'não circulante')]['valor'].sum()
        
        total_passivos = p_circulante + p_nao_circulante
        saldo_final = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum() - df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        
        liquidez = (saldo_final / total_passivos) if total_passivos > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Saldo Final", f"R$ {saldo_final:,.2f}")
        c2.metric("Total Passivos", f"R$ {total_passivos:,.2f}")
        c3.metric("Índice de Liquidez", f"{liquidez:,.2f}")
        
        st.markdown("---")
        col_a, col_b = st.columns(2)
        col_a.metric("Passivo Circulante", f"R$ {p_circulante:,.2f}")
        col_b.metric("Passivo Não Circulante", f"R$ {p_nao_circulante:,.2f}")
        
        st.markdown("### Detalhamento dos Passivos (Lançamentos)")
        # Filtra os dados apenas para mostrar o que é passivo circulante ou não circulante
        df_passivos = df_periodo[df_periodo['grupo_limpo'].isin(['circulante', 'não circulante'])]
        st.dataframe(df_passivos[['data_lancamento', 'nome_conta', 'grupo', 'valor', 'justificativa']], use_container_width=True)

    with tab3:
        st.dataframe(df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum dado encontrado para processar.")
