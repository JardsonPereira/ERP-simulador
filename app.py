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

# Inicialização de estado
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- PÁGINAS ---

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
            except Exception as e:
                st.error(f"Erro no login: {e}")

    with tab2:
        novo_email = st.text_input("Novo E-mail", key="c_email")
        nova_senha = st.text_input("Nova Senha", type="password", key="c_senha")
        if st.button("Cadastrar"):
            try:
                supabase.auth.sign_up({"email": novo_email, "password": nova_senha})
                st.success("Cadastro realizado! Verifique seu e-mail.")
            except Exception as e:
                st.error(f"Erro no cadastro: {e}")

def sistema_principal():
    st.sidebar.title("Menu Principal")
    pagina = st.sidebar.radio("Navegação", ["Dashboard", "Fluxo de Caixa"])
    
    st.sidebar.markdown("---")
    st.sidebar.write(f"👤 **Logado como:** {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        supabase.auth.sign_out()
        st.session_state.logged_in = False
        st.rerun()

    if pagina == "Dashboard":
        st.header("Bem-vindo ao Sistema Contábil")
        st.write("Use o menu lateral para acessar o Fluxo de Caixa.")

    elif pagina == "Fluxo de Caixa":
        st.header("📊 Fluxo de Caixa Dinâmico")
        user_id = st.session_state.user.id
        lancamentos = get_data_cached("lancamentos", user_id)
        contas = get_data_cached("contas", user_id)

        if lancamentos and contas:
            # Merge e Tratamento
            df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id', suffixes=('', '_conta'))
            df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
            df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
            df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
            df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()
            df['valor_efetivo'] = df.apply(lambda row: row['valor'] if row['status_limpo'] == 'Entrada' else -abs(row['valor']), axis=1)

            # Filtros
            with st.sidebar:
                st.header("⚙️ Filtros Fluxo")
                contas_disponiveis = df['nome_conta'].unique()
                contas_selecionadas = st.multiselect("Filtrar Contas:", contas_disponiveis, default=contas_disponiveis)
                d_inicio = st.date_input("Início", value=df['data_lancamento'].min())
                d_fim = st.date_input("Fim", value=df['data_lancamento'].max())
                
                # PDF
                mask_pdf = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim)
                pdf_bytes = gerar_relatorio_pdf("Fluxo de Caixa", df[mask_pdf])
                st.download_button("📥 Baixar PDF", data=pdf_bytes, file_name="fluxo.pdf")

            mask = (df['data_lancamento'] >= d_inicio) & (df['data_lancamento'] <= d_fim) & (df['nome_conta'].isin(contas_selecionadas))
            df_periodo = df[mask].copy()

            # Abas
            tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "💧 Análise de Liquidez", "📋 Detalhes"])

            with tab1:
                total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
                total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Entradas", f"R$ {total_entradas:,.2f}")
                c2.metric("Saídas", f"R$ {total_saidas:,.2f}")
                c3.metric("Saldo", f"R$ {total_entradas - total_saidas:,.2f}")
                st.line_chart(df_periodo.groupby('data_lancamento')['valor_efetivo'].sum().cumsum())

            with tab2: # Liquidez
                liquidez = (total_entradas / total_saidas) if total_saidas > 0 else (total_entradas if total_entradas > 0 else 0)
                st.metric("Índice de Liquidez", f"{liquidez:,.2f}")
                if liquidez >= 1.0: st.success("Fluxo Positivo: Receitas cobrem despesas.")
                else: st.warning("Atenção: Despesas superam receitas no período.")

            with tab3:
                st.dataframe(df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)
        else:
            st.info("Nenhum dado encontrado.")

# --- ROTEAMENTO ---
if not st.session_state.logged_in:
    login_page()
else:
    sistema_principal()
