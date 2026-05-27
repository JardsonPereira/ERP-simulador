import streamlit as st
import pandas as pd
import sys
import os
import unicodedata

# Configuração de caminhos e utilidades
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 2. Limpeza e Conversão
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)

    # Função para normalizar texto (remove acentos, espaços e padroniza para minúsculo)
    def normalizar_texto(texto):
        texto = str(texto).strip().lower()
        nfkd = unicodedata.normalize('NFKD', texto)
        return "".join([c for c in nfkd if not unicodedata.combining(c)])

    # Criar coluna auxiliar para cálculo
    df['status_norm'] = df['status_financeiro'].apply(normalizar_texto)

    # 3. Definição de sinal (1 para Entrada, -1 para Saída)
    def definir_multiplicador(status):
        if 'entrada' in status:
            return 1
        elif 'saida' in status:
            return -1
        return 0

    df['multiplicador'] = df['status_norm'].apply(definir_multiplicador)
    df['valor_efetivo'] = df['valor'] * df['multiplicador']

    # 4. Filtros de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask_periodo].copy()
    
    # 5. Cálculos do Fluxo
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio)]['valor_efetivo'].sum()
    
    entradas = df_fc[df_fc['multiplicador'] == 1]['valor'].sum()
    saidas = df_fc[df_fc['multiplicador'] == -1]['valor'].sum()
    
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 6. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {entradas:,.2f}")
    col3.metric("Saídas", f"R$ {saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.subheader("Lançamentos no Período")
    st.dataframe(
        df_fc[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']]
        .sort_values('data_lancamento', ascending=False), 
        use_container_width=True
    )

else:
    st.info("Nenhum lançamento encontrado.")
