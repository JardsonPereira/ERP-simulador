import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Razonetes e Balancete")

lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Filtro de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    df_p = df[mask]

    tab1, tab2 = st.tabs(["Razonetes (T)", "Balancete de Verificação"])
    
    with tab1:
        # (Mantive a lógica dos Razonetes conforme discutido anteriormente)
        for grupo in sorted(df_p['grupo'].unique()):
            st.markdown(f"---"); st.subheader(f"📁 {grupo}")
            contas_grupo = sorted(df_p[df_p['grupo'] == grupo]['nome_conta'].unique())
            for i in range(0, len(contas_grupo), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(contas_grupo):
                        conta = contas_grupo[i+j]
                        with col:
                            d_c = df_p[df_p['nome_conta'] == conta]
                            t_deb = d_c[d_c['operacao'] == 'DEBITO']['valor'].sum()
                            t_cre = d_c[d_c['operacao'] == 'CREDITO']['valor'].sum()
                            st.markdown(f"""
                                <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center;">
                                    <b>{conta}</b><div style="border-top: 2px solid black; margin-top: 5px;"></div>
                                    <div style="display: flex; border-left: 2px solid black; height: 60px;">
                                        <div style="flex: 1; text-align: left; padding-left: 5px; font-size: 0.85em; color: #2e7d32;"><b>D</b>: R$ {t_deb:,.2f}</div>
                                        <div style="flex: 1; text-align: right; padding-right: 5px; font-size: 0.85em; color: #c62828;"><b>C</b>: R$ {t_cre:,.2f}</div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

    with tab2:
        # Pivot Table
        pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
        pivot = pivot.reindex(columns=['DEBITO', 'CREDITO'], fill_value=0)
        
        # Cálculos de Saldo
        pivot['Saldo Devedor'] = (pivot['DEBITO'] - pivot['CREDITO']).clip(lower=0)
        pivot['Saldo Credor'] = (pivot['CREDITO'] - pivot['DEBITO']).clip(lower=0)
        
        # Adicionar linha de TOTAIS (Padrão de sistemas reais)
        totais = pivot.sum()
        totais.name = "TOTAL GERAL"
        pivot_final = pd.concat([pivot, pd.DataFrame(totais).T])
        
        # Alerta de Balancete
        if abs(pivot_final.loc['TOTAL GERAL', 'DEBITO'] - pivot_final.loc['TOTAL GERAL', 'CREDITO']) > 0.01:
            st.error("⚠️ O Balancete NÃO está fechado! (Débito ≠ Crédito)")
        else:
            st.success("✅ Balancete fechado com sucesso.")

        # Exibição Profissional
        st.dataframe(pivot_final.style.format("R$ {:,.2f}")
                     .map(lambda v: 'background-color: #f0f2f6; font-weight: bold', subset=pd.IndexSlice[['TOTAL GERAL'], :])
                     .map(lambda v: 'background-color: #d4edda; color: #155724; font-weight: bold' if v > 0 else '', subset=['Saldo Devedor'])
                     .map(lambda v: 'background-color: #f8d7da; color: #721c24; font-weight: bold' if v > 0 else '', subset=['Saldo Credor']),
                     use_container_width=True)
else:
    st.info("Sem dados para exibir.")
