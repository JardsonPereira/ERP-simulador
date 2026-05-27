import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o caminho das utilidades
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

# 1. Carregamento e Preparação dos Dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # Garantir que o valor seja numérico
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])

    # 2. Lógica de Identificação (O "coração" da reflexão automática)
    def normalizar_e_dar_sinal(status):
        # Transforma tudo em minúsculo e remove acentos para evitar falhas
        s = str(status).strip().lower().replace('ã', 'a')
        if 'entrada' in s:
            return 1  # Multiplicador positivo
        elif 'saida' in s:
            return -1 # Multiplicador negativo
        return 0

    # Aplica o multiplicador ao status
    df['multiplicador'] = df['status_financeiro'].apply(normalizar_e_dar_sinal)
    # Calcula o valor efetivo: 100 * 1 = 100 | 100 * -1 = -100
    df['valor_efetivo'] = df['valor'] * df['multiplicador']

    # --- DEBUG: Verificação obrigatória ---
    # Se o 'multiplicador' for 0, o nome no banco é diferente de Entrada/Saída
    with st.expander("🛠️ Diagnóstico: Validar Status (Clique aqui)"):
        st.write("Dados processados:", df[['status_financeiro', 'valor', 'multiplicador', 'valor_efetivo']])

    # 3. Filtros
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask].copy()

    # 4. Cálculos
    # Saldo Inicial: Soma de todos os valores efetivos anteriores à data de início
    saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    
    # Totais do período
    total_entradas = df_fc[df_fc['multiplicador'] == 1]['valor'].sum()
    total_saidas = df_fc[df_fc['multiplicador'] == -1]['valor'].sum()
    
    # Saldo final = Saldo inicial + todas as variações efetivas do período
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 5. Exibição
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.dataframe(df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum lançamento encontrado para exibir.")
