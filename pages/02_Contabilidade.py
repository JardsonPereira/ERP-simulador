import streamlit as st, pandas as pd, sys, os

# 1. Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

# 2. Inicialização
check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Razonetes Contábeis")

# 3. Carregar Dados
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
    df_periodo = df[mask]

    tab_r, tab_b = st.tabs(["Razonetes (T)", "Balancete"])
    
    with tab_r:
        for grupo in sorted(df_periodo['grupo'].unique()):
            st.markdown(f"### 📁 {grupo}")
            df_grupo = df_periodo[df_periodo['grupo'] == grupo]
            
            for nome_conta in sorted(df_grupo['nome_conta'].unique()):
                d_conta = df_grupo[df_grupo['nome_conta'] == nome_conta]
                
                # Visual do Razonete em T
                st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:1.2em;'>{nome_conta}</div>", unsafe_allow_html=True)
                
                # Barra horizontal superior do T
                st.markdown("<hr style='margin:0; border:1px solid #333;'>", unsafe_allow_html=True)
                
                col_t1, col_t2 = st.columns(2)
                deb = d_conta[d_conta['operacao'] == 'DEBITO'][['justificativa', 'valor']]
                cre = d_conta[d_conta['operacao'] == 'CREDITO'][['justificativa', 'valor']]
                
                with col_t1:
                    st.markdown("<div style='text-align:center;'>DÉBITO</div>", unsafe_allow_html=True)
                    if not deb.empty: st.dataframe(deb, hide_index=True, use_container_width=True)
                    else: st.caption("—")
                
                with col_t2:
                    st.markdown("<div style='text-align:center;'>CRÉDITO</div>", unsafe_allow_html=True)
                    if not cre.empty: st.dataframe(cre, hide_index=True, use_container_width=True)
                    else: st.caption("—")
                
                # Fechamento do T
                st.markdown("<div style='border-left:1px solid #333; height:20px; margin-left:50%;'></div>", unsafe_allow_html=True)
                saldo = deb['valor'].sum() - cre['valor'].sum()
                st.markdown(f"<div style='text-align:center;'><strong>Saldo: R$ {saldo:,.2f}</strong></div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

    with tab_b:
        pivot = df_periodo.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
        if 'DEBITO' not in pivot.columns: pivot['DEBITO'] = 0
        if 'CREDITO' not in pivot.columns: pivot['CREDITO'] = 0
        
        pivot['Saldo Devedor'] = pivot.apply(lambda x: x['DEBITO'] - x['CREDITO'] if x['DEBITO'] > x['CREDITO'] else 0, axis=1)
        pivot['Saldo Credor'] = pivot.apply(lambda x: x['CREDITO'] - x['DEBITO'] if x['CREDITO'] > x['DEBITO'] else 0, axis=1)
        
        # Correção do erro: Usando .map no lugar de .applymap
        st.dataframe(pivot.style.format("R$ {:,.2f}")
                     .map(lambda v: 'background-color: #d4edda; color: #155724; font-weight: bold' if v > 0 else '', subset=['Saldo Devedor'])
                     .map(lambda v: 'background-color: #f8d7da; color: #721c24; font-weight: bold' if v > 0 else '', subset=['Saldo Credor']),
                     use_container_width=True)
else:
    st.info("Sem dados para exibir.")
