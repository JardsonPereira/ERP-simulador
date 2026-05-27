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

# 1. Carregamento dos dados
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 2. Limpeza e Padronização
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['status_limpo'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()
    
    # 3. FILTRO RÍGIDO: Remove qualquer status que não seja Entrada ou Saída
    # Isso elimina automaticamente "Transação Interna" ou outros status indesejados
    df = df[df['status_limpo'].isin(['Entrada', 'Saída'])].copy()

    # 4. Cálculo do Valor Efetivo (Entrada = +, Saída = -)
    def calcular_efetivo(row):
        # abs(valor) garante que, se alguém digitou negativo por erro, vira positivo
        # o sinal de menos (-) na frente do abs() garante a subtração na saída
        if row['status_limpo'] == 'Entrada':
            return abs(row['valor'])
        else:
            return -abs(row['valor'])

    df['valor_efetivo'] = df.apply(calcular_efetivo, axis=1)

    # 5. Filtros de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date() if not df.empty else pd.Timestamp.now().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date() if not df.empty else pd.Timestamp.now().date())
    
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_fc = df[mask].copy()

    # 6. Cálculos Financeiros
    # Saldo inicial: Acumulado de tudo o que aconteceu antes do filtro de data
    saldo_inicial = df[df['data_lancamento'].dt.date < d_inicio]['valor_efetivo'].sum()
    
    # Totais para exibição (usamos o valor absoluto para mostrar o montante)
    total_entradas = df_fc[df_fc['status_limpo'] == 'Entrada']['valor'].sum()
    total_saidas = df_fc[df_fc['status_limpo'] == 'Saída']['valor'].sum()
    
    # Saldo final: O saldo que já existia + as movimentações do período (já subtraindo as saídas)
    saldo_final = saldo_inicial + df_fc['valor_efetivo'].sum()

    # 7. Exibição das métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    st.markdown("---")
    st.subheader("Lançamentos no Período")
    # Tabela mostrando apenas o que foi filtrado
    st.dataframe(
        df_fc[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']]
        .sort_values('data_lancamento', ascending=False), 
        use_container_width=True
    )

else:
    st.info("Nenhum lançamento de Entrada/Saída encontrado.")
