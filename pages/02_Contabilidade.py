import streamlit as st, pandas as pd, sys, os

# 1. Configurar caminho para encontrar utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

# 2. Inicialização
check_auth()
inject_css()
supabase = get_supabase()

st.header("📚 Contabilidade")

# 3. Carregar Dados
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    # Preparar DataFrame consolidado
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
            
            # Preparar dados para o Razonete
            deb_df = per[per['operacao'] == 'DEBITO'][['data_lancamento', 'justificativa', 'valor']]
            cre_df = per[per['operacao'] == 'CREDITO'][['data_lancamento', 'justificativa', 'valor']]
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown("<div style='background-color:#e8f5e9; padding:10px; border-top: 3px solid #2e7d32; text-align:center;'><strong>DÉBITOS</strong></div>", unsafe_allow_html=True)
                st.dataframe(deb_df, hide_index=True, use_container_width=True)
            
            with col_t2:
                st.markdown("<div style='background-color:#ffebee; padding:10px; border-top: 3px solid #c62828; text-align:center;'><strong>CRÉDITOS</strong></div>", unsafe_allow_html=True)
                st.dataframe(cre_df, hide_index=True, use_container_width=True)
            
            # Cálculo de Saldo Final
            saldo_final = deb_df['valor'].sum() - cre_df['valor'].sum()
            
            st.markdown(f"""
                <div style='text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-bottom: 20px;'>
                    <strong>Saldo Atual: R$ {saldo_final:,.2f}</strong>
                </div>
            """, unsafe_allow_html=True)
            st.divider()

    with tab_b:
        # Pivot table para Balancete
        pivot = df[mask_periodo].pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
        
        if 'DEBITO' not in pivot.columns: pivot['DEBITO'] = 0
        if 'CREDITO' not in pivot.columns: pivot['CREDITO'] = 0
        
        # Calcular saldos destacados
        pivot['Saldo Devedor'] = pivot.apply(lambda x: x['DEBITO'] - x['CREDITO'] if x['DEBITO'] > x['CREDITO'] else 0, axis=1)
        pivot['Saldo Credor'] = pivot.apply(lambda x: x['CREDITO'] - x['DEBITO'] if x['CREDITO'] > x['DEBITO'] else 0, axis=1)
        
        # Estilização Condicional
        def highlight_saldos(row):
            styles = [''] * len(row)
            if row['Saldo Devedor'] > 0:
                styles[row.index.get_loc('Saldo Devedor')] = 'background-color: #c8e6c9; color: #2e7d32; font-weight: bold'
            if row['Saldo Credor'] > 0:
                styles[row.index.get_loc('Saldo Credor')] = 'background-color: #ffcdd2; color: #c62828; font-weight: bold'
            return styles

        st.dataframe(pivot.style.apply(highlight_saldos, axis=1).format("R$ {:,.2f}"), use_container_width=True)
        
else:
    st.info("Sem dados para exibir.")
