import streamlit as st
import pandas as pd
import sys
import os

# Configuração do caminho para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

# Autenticação e Estilo
check_auth()
inject_css()

st.header("💵 Fluxo de Caixa Detalhado")

# Carregar dados do Supabase via cache
user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    # 1. Preparação dos dados
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # 2. Filtro de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    
    # 3. Filtrar apenas o que é "Entrada" ou "Saída"
    # Criamos uma coluna de valor efetivo para cálculo matemático
    df['valor_efetivo'] = df.apply(
        lambda x: x['valor'] if x['status_financeiro'] == 'Entrada' 
        else (-x['valor'] if x['status_financeiro'] == 'Saída' else 0), 
        axis=1
    )
    
    # Mascaras para o período
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    mask_valido = df['status_financeiro'].isin(['Entrada', 'Saída'])
    
    # Dados para exibição
    df_fc = df[mask_periodo & mask_valido].copy()
    
    # 4. Cálculo do Saldo Inicial (acumulado antes do período escolhido)
    saldo_inicial = df[(df['data_lancamento'].dt.date < d_inicio) & mask_valido]['valor_efetivo'].sum()
    
    # 5. Exibição das Métricas
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
    col2.metric("Entradas", f"R$ {df_fc[df_fc['status_financeiro'] == 'Entrada']['valor'].sum():,.2f}")
    col3.metric("Saídas", f"R$ {df_fc[df_fc['status_financeiro'] == 'Saída']['valor'].sum():,.2f}")
    col4.metric("Saldo Final", f"R$ {(saldo_inicial + df_fc['valor_efetivo'].sum()):,.2f}")
    
    # 6. Tabela
    st.subheader("Lançamentos no Período")
    st.dataframe(
        df_fc[['data_lancamento', 'nome_conta', 'status_financeiro', 'valor', 'justificativa']], 
        use_container_width=True,
        column_config={
            "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")
        }
    )
    
    # 7. Download PDF
    if st.download_button("Baixar Fluxo de Caixa PDF", data=gerar_relatorio_pdf("Fluxo de Caixa", df_fc), file_name="fluxo_caixa.pdf"):
        st.success("Download iniciado!")
        
else:
    st.info("Nenhum lançamento com status 'Entrada' ou 'Saída' encontrado para o período.")
