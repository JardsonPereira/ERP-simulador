import streamlit as st
import pandas as pd
from utils import get_data_cached, check_auth, get_supabase

check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📋 Relatório Contábil Consolidado")

# 1. Carregar Dados
lanc = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lanc and contas:
    df = pd.DataFrame(lanc).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    df['grupo'] = df.get('grupo_lanc', df.get('grupo_conta', 'Outros'))
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

    # 2. Filtro de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início do Relatório", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim do Relatório", value=df['data_lancamento'].max().date())
    
    df_p = df[(df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)].copy()

    # --- CÁLCULOS ---
    # DRE
    rec = df_p[df_p['grupo'].str.contains('Receita', case=False, na=False)]['valor'].sum()
    desp = df_p[df_p['grupo'].str.contains('Despesa|Custo', case=False, na=False)]['valor'].sum()
    lucro = rec - desp

    # Balanço (Resumo)
    ativo = df_p[df_p['grupo'].str.contains('Ativo', case=False, na=False)]['valor'].sum()
    passivo = df_p[df_p['grupo'].str.contains('Passivo', case=False, na=False)]['valor'].sum()

    # Fluxo
    fluxo = df_p[df_p['status_financeiro'].isin(['Entrada', 'Saída'])].copy()
    fluxo['val_efetivo'] = fluxo.apply(lambda x: x['valor'] if x['status_financeiro']=='Entrada' else -x['valor'], axis=1)
    net_fluxo = fluxo['val_efetivo'].sum()

    # 3. Exibição
    st.subheader("Resumo do Período")
    col1, col2, col3 = st.columns(3)
    col1.metric("Lucro (DRE)", f"R$ {lucro:,.2f}")
    col2.metric("Saldo Líquido (Fluxo)", f"R$ {net_fluxo:,.2f}")
    col3.metric("Patrimônio Líquido", f"R$ {(ativo - passivo):,.2f}")

    st.markdown("---")
    
    # Detalhamento
    tab1, tab2, tab3 = st.tabs(["DRE Simplificada", "Posição Patrimonial", "Resumo Fluxo"])
    
    with tab1:
        st.write("### DRE")
        st.table(pd.DataFrame({"Descrição": ["Receitas", "Despesas/Custos", "Resultado"], "Valor": [rec, desp, lucro]}))
    
    with tab2:
        st.write("### Balanço (Resumo)")
        st.table(pd.DataFrame({"Descrição": ["Ativos", "Passivos", "PL"], "Valor": [ativo, passivo, (ativo-passivo)]}))
        
    with tab3:
        st.write("### Fluxo de Caixa")
        st.dataframe(fluxo[['data_lancamento', 'status_financeiro', 'valor', 'justificativa']], use_container_width=True)

else:
    st.info("Aguardando lançamentos...")
