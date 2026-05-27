import streamlit as st
import pandas as pd

# Função para garantir a padronização dos status
def formatar_status(status):
    if isinstance(status, str):
        return status.strip().capitalize()
    return "Outros"

# Supondo que 'lancamentos' e 'contas' já venham do seu banco de dados
if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 1. Padronização e Limpeza
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    df['status_financeiro'] = df['status_financeiro'].apply(formatar_status)
    
    # 2. Definição do Valor Efetivo (Onde a mágica acontece)
    # Entrada soma (+) | Saída subtrai (-)
    def calcular_efetivo(row):
        if row['status_financeiro'] == 'Entrada':
            return row['valor']
        elif row['status_financeiro'] == 'Saída':
            return -abs(row['valor']) # O abs garante que o valor seja subtraído
        return 0

    df['valor_efetivo'] = df.apply(calcular_efetivo, axis=1)

    # 3. Filtros do Usuário
    st.subheader("Fluxo de Caixa")
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    # Máscaras
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    
    # 4. Cálculos Automáticos
    # Saldo inicial é tudo o que aconteceu ANTES da data de início
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio)]['valor_efetivo'].sum()
    
    # Movimentações no período selecionado
    df_periodo = df[mask_periodo].copy()
    
    total_entradas = df_periodo[df_periodo['status_financeiro'] == 'Entrada']['valor'].sum()
    total_saidas = df_periodo[df_periodo['status_financeiro'] == 'Saída']['valor'].sum()
    saldo_final = saldo_inicial + df_periodo['valor_efetivo'].sum()

    # 5. Exibição das Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col3.metric("Saídas", f"R$ {total_saidas:,.2f}", delta_color="inverse")
    col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")

    # Tabela de detalhamento
    st.dataframe(df_periodo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.warning("Não há dados de lançamentos ou contas para processar.")
