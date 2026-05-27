import streamlit as st
import pandas as pd
import sys
import os

# Ajuste de caminho para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

# Inicialização
check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

# 1. Carregamento de Dados
# Definimos as variáveis antes de qualquer condicional para evitar o NameError
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

# 2. Validação dos dados
if lancamentos and contas:
    df_l = pd.DataFrame(lancamentos)
    df_c = pd.DataFrame(contas)
    
    # Merge com tratamento de colunas
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # 3. Limpeza e Padronização
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_financeiro'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()

    # Função para cálculo de valor efetivo
    def calcular_efetivo(row):
        valor = float(row['valor'])
        if row['status_financeiro'] == 'Entrada':
            return valor
        elif row['status_financeiro'] == 'Saída':
            return -abs(valor) # Garante valor negativo para saídas
        return 0

    df['valor_efetivo'] = df.apply(calcular_efetivo, axis=1)

    # 4. Interface do Fluxo
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    # Filtros
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    mask_valido = df['status_financeiro'].isin(['Entrada', 'Saída'])
    
    # Cálculos
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio) & mask_valido]['valor_efetivo'].sum()
    df_fc = df[mask_periodo & mask_valido].copy()
    
    entradas = df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum()
    saidas = df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum()
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 5. Exibição de Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {entradas:,.2f}")
    col3.metric("Saídas", f"R$ {saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.subheader("Detalhamento")
    st.dataframe(df_fc[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Nenhum dado encontrado. Verifique se existem lançamentos registrados.")
