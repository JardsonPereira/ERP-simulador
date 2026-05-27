import streamlit as st
import pandas as pd
import sys
import os

# Caminho para utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa e Liquidez")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df_l = pd.DataFrame(lancamentos)
    df_c = pd.DataFrame(contas)
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # Padronização profunda
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()

    # --- 2. CÁLCULO DE LIQUIDEZ (Baseado em todo o histórico) ---
    # Ativo Circulante / Passivo Circulante
    ativo_circ = df[df['status_financeiro'] == 'Ativo Circulante']['valor'].sum()
    passivo_circ = df[df['status_financeiro'] == 'Passivo Circulante']['valor'].sum()
    liquidez = (ativo_circ / passivo_circ) if passivo_circ > 0 else 0
    
    st.subheader("Indicadores")
    c_liq, c_ativ, c_pass = st.columns(3)
    c_liq.metric("Liquidez Corrente", f"{liquidez:.2f}")
    c_ativ.metric("Total Ativos Circ.", f"R$ {ativo_circ:,.2f}")
    c_pass.metric("Total Passivos Circ.", f"R$ {passivo_circ:,.2f}")
    st.markdown("---")

    # --- 3. FILTRO RÍGIDO DE FLUXO (Apenas Entrada/Saída) ---
    df_fluxo = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    # Lógica de sinal
    df_fluxo['sinal'] = df_fluxo['status_limpo'].apply(lambda x: 1 if x == 'Entrada' else -1)
    df_fluxo['valor_efetivo'] = df_fluxo['valor'] * df_fluxo['sinal']

    # 4. Interface e Filtros de Data Rígidos
    st.subheader("Fluxo de Caixa por Data")
    c1, c2 = st.columns(2)
    data_min = df_fluxo['data_lancamento'].min().date() if not df_fluxo.empty else pd.Timestamp.now().date()
    data_max = df_fluxo['data_lancamento'].max().date() if not df_fluxo.empty else pd.Timestamp.now().date()
    
    d_inicio = c1.date_input("Início", value=data_min)
    d_fim = c2.date_input("Fim", value=data_max)
    
    # Filtro de datas exato
    mask = (df_fluxo['data_lancamento'].dt.date >= d_inicio) & (df_fluxo['data_lancamento'].dt.date <= d_fim)
    df_periodo = df_fluxo[mask].copy()

    # 5. Cálculos do Fluxo
    saldo_inicial = df_fluxo[df_fluxo['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    total_ent = df_periodo[df_periodo['sinal'] == 1]['valor'].sum()
    total_sai = df_periodo[df_periodo['sinal'] == -1]['valor'].sum()
    saldo_final = saldo_inicial + df_periodo['valor_efetivo'].sum()

    # 6. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_ent:,.2f}")
    col3.metric("Saídas", f"R$ {total_sai:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.dataframe(df_periodo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']].sort_values('data_lancamento'), use_container_width=True)

else:
    st.info("Nenhum dado encontrado para processar.")
