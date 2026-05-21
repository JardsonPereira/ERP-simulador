import streamlit as st, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Contabilidade")
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Filtro de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    
    tab_r, tab_b = st.tabs(["Razonetes (T)", "Balancete de Verificação"])
    
    with tab_r:
        grupos_disponiveis = df['grupo'].unique()
        grupo_selecionado = st.selectbox("Selecione o Grupo:", grupos_disponiveis)
        df_g = df[df['grupo'] == grupo_selecionado]
        
        for nome_conta in df_g['nome_conta'].unique():
            d_conta = df_g[df_g['nome_conta'] == nome_conta]
            per = d_conta[mask_periodo]
            
            st.markdown(f"### {nome_conta}")
            col_t1, col_t2 = st.columns(2)
            
            # Layout em T
            deb_df = per[per['operacao'] == 'DEBITO'][['data_lancamento', 'justificativa', 'valor']]
            cre_df = per[per['operacao'] == 'CREDITO'][['data_lancamento', 'justificativa', 'valor']]
            
            with col_t1:
                st.markdown("<div style='background-color:#e8f5e9; padding:10px; border-top: 3px solid #2e7d32;'><strong>DÉBITOS</strong></div>", unsafe_allow_html=True)
                if not deb_df.empty: st.table(deb_df)
                else: st.write("Nenhum débito.")
            
            with col_t2:
                st.markdown("<div style='background-color:#ffebee; padding:10px; border-top: 3px solid #c62828;'><strong>CRÉDITOS</strong></div>", unsafe_allow_html=True)
                if not cre_df.empty: st.table(cre_df)
                else: st.write("Nenhum crédito.")
            
            st.divider()

    with tab_b:
        # Cálculo do Balancete
        pivot = df[mask_periodo].pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
        
        # Garantir colunas DEBITO e CREDITO
        if 'DEBITO' not in pivot.columns: pivot['DEBITO'] = 0
        if 'CREDITO' not in pivot.columns: pivot['CREDITO'] = 0
        
        # Calcular Saldos
        pivot['Saldo Devedor'] = pivot.apply(lambda x: x['DEBITO'] - x['CREDITO'] if x['DEBITO'] > x['CREDITO'] else 0, axis=1)
        pivot['Saldo Credor'] = pivot.apply(lambda x: x['CREDITO'] - x['DEBITO'] if x['CREDITO'] > x['DEBITO'] else 0, axis=1)
        
        # Estilização
        st.dataframe(pivot.style.format("R$ {:,.2f}")
                     .highlight_max(subset=['Saldo Devedor', 'Saldo Credor'], color='lightyellow')
                     .applymap(lambda v: 'color: green; font-weight: bold' if v > 0 else '', subset=['Saldo Devedor'])
                     .applymap(lambda v: 'color: red; font-weight: bold' if v > 0 else '', subset=['Saldo Credor']),
                     use_container_width=True)
        
else:
    st.info("Sem dados para exibir.")
