import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Contabilidade Completa")

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

    # Abas
    tab1, tab2, tab3 = st.tabs(["Razonetes (T)", "Balancete", "Balanço Patrimonial"])
    
    with tab1:
        for grupo in sorted(df_p['grupo'].unique()):
            st.markdown("---"); st.subheader(f"📁 {grupo}")
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
        pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
        pivot = pivot.reindex(columns=['DEBITO', 'CREDITO'], fill_value=0)
        pivot['Saldo Devedor'] = (pivot['DEBITO'] - pivot['CREDITO']).clip(lower=0)
        pivot['Saldo Credor'] = (pivot['CREDITO'] - pivot['DEBITO']).clip(lower=0)
        
        totais = pivot.sum()
        pivot_final = pd.concat([pivot, pd.DataFrame(totais.rename("TOTAL")).T])
        
        if abs(pivot_final.loc['TOTAL', 'DEBITO'] - pivot_final.loc['TOTAL', 'CREDITO']) > 0.01:
            st.error("⚠️ Balancete desbalanceado!")
        else:
            st.success("✅ Balancete fechado.")
        st.dataframe(pivot_final.style.format("R$ {:,.2f}"), use_container_width=True)

    with tab3:
        # Lógica do Balanço
        pivot_balanco = df_p.pivot_table(index=['grupo', 'nome_conta'], columns='operacao', values='valor', aggfunc='sum', fill_value=0)
        pivot_balanco['Saldo'] = pivot_balanco.get('DEBITO', 0) - pivot_balanco.get('CREDITO', 0)
        
        # Categorização simples (Ajuste os nomes conforme seu grupo)
        def definir_tipo(grupo):
            g = grupo.lower()
            if 'ativo' in g: return 'Ativo'
            if 'passivo' in g: return 'Passivo'
            return 'PL'

        pivot_balanco['Tipo'] = pivot_balanco.index.get_level_values('grupo').map(definir_tipo)
        
        # Totais por tipo
        resumo = pivot_balanco.groupby('Tipo')['Saldo'].sum()
        
        col_a, col_p, col_pl = st.columns(3)
        col_a.metric("Ativo Total", f"R$ {resumo.get('Ativo', 0):,.2f}")
        col_p.metric("Passivo Total", f"R$ {abs(resumo.get('Passivo', 0)):,.2f}")
        col_pl.metric("Patrimônio Líquido", f"R$ {abs(resumo.get('PL', 0)):,.2f}")
        
        # Equação fundamental
        ativo = resumo.get('Ativo', 0)
        passivo_pl = abs(resumo.get('Passivo', 0)) + abs(resumo.get('PL', 0))
        
        st.divider()
        if abs(ativo - passivo_pl) < 0.01:
            st.success(f"Equação Equilibrada: Ativo (R${ativo:,.2f}) = Passivo + PL (R${passivo_pl:,.2f})")
        else:
            st.error(f"Diferença encontrada: Ativo (R${ativo:,.2f}) ≠ Passivo + PL (R${passivo_pl:,.2f})")

        st.dataframe(pivot_balanco, use_container_width=True)

else:
    st.info("Sem dados para exibir.")
