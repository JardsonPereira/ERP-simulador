import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Razonetes")

lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Filtro
    d_inicio = st.date_input("Início", value=df['data_lancamento'].min().date())
    mask = (df['data_lancamento'].dt.date >= d_inicio)
    df_p = df[mask]

    for grupo in sorted(df_p['grupo'].unique()):
        st.markdown(f"---")
        st.subheader(f"📁 {grupo}")
        
        # Grid de Razonetes
        contas_grupo = sorted(df_p[df_p['grupo'] == grupo]['nome_conta'].unique())
        
        for i in range(0, len(contas_grupo), 3):
            cols = st.columns(3)
            for j, col in enumerate(cols):
                if i + j < len(contas_grupo):
                    conta = contas_grupo[i+j]
                    with col:
                        # Dados
                        d_c = df_p[df_p['nome_conta'] == conta]
                        total_deb = d_c[d_c['operacao'] == 'DEBITO']['valor'].sum()
                        total_cre = d_c[d_c['operacao'] == 'CREDITO']['valor'].sum()
                        
                        # Layout do T com D/C e Cores
                        st.markdown(f"""
                            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center;">
                                <b>{conta}</b>
                                <div style="border-top: 2px solid black; margin-top: 5px;"></div>
                                <div style="display: flex; border-left: 2px solid black; height: 60px;">
                                    <div style="flex: 1; text-align: left; padding-left: 5px; font-size: 0.85em; color: #2e7d32;">
                                        <b>D</b>: R$ {total_deb:,.2f}
                                    </div>
                                    <div style="flex: 1; text-align: right; padding-right: 5px; font-size: 0.85em; color: #c62828;">
                                        <b>C</b>: R$ {total_cre:,.2f}
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

    # Balancete
    st.markdown("## Balancete de Verificação")
    pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
    if 'DEBITO' not in pivot.columns: pivot['DEBITO'] = 0
    if 'CREDITO' not in pivot.columns: pivot['CREDITO'] = 0
    pivot['Saldo Devedor'] = pivot.apply(lambda x: x['DEBITO'] - x['CREDITO'] if x['DEBITO'] > x['CREDITO'] else 0, axis=1)
    pivot['Saldo Credor'] = pivot.apply(lambda x: x['CREDITO'] - x['DEBITO'] if x['CREDITO'] > x['DEBITO'] else 0, axis=1)
    
    st.dataframe(pivot.style.format("R$ {:,.2f}")
                 .map(lambda v: 'background-color: #d4edda; color: #155724; font-weight: bold' if v > 0 else '', subset=['Saldo Devedor'])
                 .map(lambda v: 'background-color: #f8d7da; color: #721c24; font-weight: bold' if v > 0 else '', subset=['Saldo Credor']),
                 use_container_width=True)

else:
    st.info("Sem dados para exibir.")
