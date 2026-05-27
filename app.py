import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# Carregar variáveis do arquivo .env
load_dotenv()

# Conexão com Supabase usando .env
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="Sistema Contábil", layout="wide")
inject_css()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    st.title("Sistema Contábil - Login")
    tab1, tab2 = st.tabs(["Login", "Cadastrar"])
    with tab1:
        email = st.text_input("E-mail", key="l_email")
        senha = st.text_input("Senha", type="password", key="l_senha")
        if st.button("Entrar"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                st.session_state.logged_in = True
                st.session_state.user = res.user
                st.rerun()
            except Exception as e: st.error(f"Erro: {e}")
    with tab2:
        novo_email = st.text_input("Novo E-mail", key="c_email")
        nova_senha = st.text_input("Nova Senha", type="password", key="c_senha")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado!")
            except Exception as e: st.error(f"Erro: {e}")

def sistema_principal():
    st.sidebar.title("Menu Principal")
    pagina = st.sidebar.radio("Navegação", ["Dashboard", "Fluxo de Caixa"])
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 Logado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.rerun()

    if pagina == "Fluxo de Caixa":
        st.header("📊 Fluxo de Caixa: Liquidez e Passivos")
        user_id = st.session_state.user.id
        lancamentos = get_data_cached("lancamentos", user_id)
        contas = get_data_cached("contas", user_id)

        if lancamentos and contas:
            df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
            df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
            df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

            with st.sidebar:
                st.header("⚙️ Filtros")
                d_inicio = st.date_input("Início", value=df['data_lancamento'].min())
                d_fim = st.date_input("Fim", value=df['data_lancamento'].max())

            mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim)
            df_periodo = df[mask].copy()

            tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "💧 Liquidez e Passivos", "📋 Detalhes"])

            with tab1:
                total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
                total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Entradas", f"R$ {total_entradas:,.2f}")
                c2.metric("Saídas", f"R$ {total_saidas:,.2f}")
                c3.metric("Saldo", f"R$ {total_entradas - total_saidas:,.2f}")

            with tab2: # Aba Focada em Liquidez e Passivos
                st.subheader("Análise de Solvência")
                entradas_ativo = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
                passivos_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
                
                # Índice de Liquidez (Entradas / Passivos)
                liquidez = (entradas_ativo / passivos_saidas) if passivos_saidas > 0 else (entradas_ativo if entradas_ativo > 0 else 0)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Disponível (Ativos)", f"R$ {entradas_ativo:,.2f}")
                col2.metric("Passivos (Saídas)", f"R$ {passivos_saidas:,.2f}")
                col3.metric("Índice de Liquidez", f"{liquidez:,.2f}")
                
                st.info("O Índice de Liquidez mostra quantas vezes suas entradas cobrem seus passivos (saídas) no período selecionado.")

            with tab3:
                st.dataframe(df_periodo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

if not st.session_state.logged_in:
    login_page()
else:
    sistema_principal()
