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
    # Merge garantindo que temos os tipos de conta
    df_lanc = pd.DataFrame(lancamentos)
    df_conta = pd.DataFrame(contas)
    df = df_lanc.merge(df_conta, left_on='conta_id', right_on='id', suffixes=('', '_conta'))
    
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'].astype(str).str[:10]).dt.date
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
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
    tab1, tab2, tab3 = st.tabs(["📈 Visão Geral", "💧 Liquidez", "📋 Detalhes"])

    with tab1: # VISÃO GERAL
        total_entradas = df_periodo[df_periodo['status_limpo'] == 'Entrada']['valor'].sum()
        total_saidas = df_periodo[df_periodo['status_limpo'] == 'Saída']['valor'].sum()
        saldo = total_entradas - total_saidas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", f"R$ {total_entradas:,.2f}")
        c2.metric("Saídas", f"R$ {total_saidas:,.2f}")
        c3.metric("Saldo", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

        st.markdown("### Evolução Diária")
        chart_data = df_periodo.groupby('data_lancamento')['valor'].sum().reset_index()
        st.line_chart(chart_data.set_index('data_lancamento'))

    with tab3: # DETALHES
        st.subheader("Lançamentos Detalhados")
        st.dataframe(df_periodo[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

    with tab2: # LIQUIDEZ (NOVA)
        st.subheader("Análise de Liquidez (Ativo vs Passivo)")
        
        # IMPORTANTE: Aqui assumimos que a tabela 'contas' tem a coluna 'tipo_conta'
        # Se 'tipo_conta' não existir, o sistema não saberá o que é ativo ou passivo.
        if 'tipo_conta' in df_periodo.columns:
            ativo = df_periodo[df_periodo['tipo_conta'] == 'Ativo']['valor'].sum()
            passivo = df_periodo[df_periodo['tipo_conta'] == 'Passivo']['valor'].sum()
            
            liquidez_corrente = (ativo / passivo) if passivo > 0 else (ativo if ativo > 0 else 0)
            
            col_l1, col_l2, col_l3 = st.columns(3)
            col_l1.metric("Total Ativos", f"R$ {ativo:,.2f}")
            col_l2.metric("Total Passivos", f"R$ {passivo:,.2f}")
            col_l3.metric("Índice de Liquidez", f"{liquidez_corrente:,.2f}")
            
            # Feedback visual baseado na liquidez
            if liquidez_corrente > 1.5:
                st.success("Excelente! Sua liquidez está alta. Você possui folga financeira.")
            elif liquidez_corrente >= 1:
                st.warning("Equilibrado. Seus ativos cobrem seus passivos, mas atenção ao fluxo.")
            else:
                st.error("Atenção! Sua liquidez está abaixo de 1. O volume de passivos supera seus ativos imediatos.")
        else:
            st.error("Para calcular a liquidez, adicione a coluna 'tipo_conta' (Ativo/Passivo) na sua tabela 'contas' no Supabase.")

else:
    st.warning("Nenhum dado encontrado.")
