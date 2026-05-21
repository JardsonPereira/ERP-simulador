import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, check_auth

# Inicialização
check_auth()
supabase = get_supabase()

st.header("📝 Lançamentos Realizados")

# Carregar dados
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    # Converter para DataFrame
    df_l = pd.DataFrame(lancamentos)
    df_c = pd.DataFrame(contas)
    
    # Merge para trazer o nome da conta junto com o lançamento
    df = df_l.merge(df_c[['id', 'nome_conta']], left_on='conta_id', right_on='id', how='left')
    
    # Seleção das colunas de exibição (incluindo justificativa)
    colunas_exibicao = ['data_lancamento', 'nome_conta', 'operacao', 'valor', 'justificativa']
    df_exibicao = df[colunas_exibicao].sort_values(by='data_lancamento', ascending=False)
    
    # Formatação das colunas para melhor leitura
    df_exibicao = df_exibicao.rename(columns={
        'data_lancamento': 'Data',
        'nome_conta': 'Conta',
        'operacao': 'Operação',
        'valor': 'Valor (R$)',
        'justificativa': 'Justificativa'
    })

    # Exibição com ajuste de largura automática
    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Valor (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            "Justificativa": st.column_config.TextColumn("Justificativa", width="large")
        }
    )
else:
    st.info("Nenhum lançamento encontrado.")
