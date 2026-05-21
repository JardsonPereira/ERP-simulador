import streamlit as st, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css
check_auth(); inject_css()
st.header("📚 Contabilidade")
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    
    tab_r, tab_b = st.tabs(["Razonetes", "Balancete"])
    with tab_r:
        grupos_disponiveis = df['grupo'].unique()
        grupo_selecionado = st.selectbox("Selecione o Grupo:", grupos_disponiveis)
        df_g = df[df['grupo'] == grupo_selecionado]
        for nome_conta in df_g['nome_conta'].unique():
            d_conta = df_g[df_g['nome_conta'] == nome_conta]
            ant = d_conta[d_conta['data_lancamento'].dt.date < d_inicio]
            per = d_conta[mask_periodo]
            deb = per[per['operacao'] == 'DEBITO']['valor'].sum()
            cre = per[per['operacao'] == 'CREDITO']['valor'].sum()
            saldo_ini = ant[ant['operacao'] == 'DEBITO']['valor'].sum() - ant[ant['operacao'] == 'CREDITO']['valor'].sum()
            saldo_fin = abs(saldo_ini + deb - cre)
            st.markdown(f"""
                <div class="t-account">
                    <div class="t-title">{nome_conta} (Ini: {saldo_ini:,.2f})</div>
                    <table style="width:100%">
                        <tr><td style="text-align:center; border-right:1px solid #ddd">Débito</td><td style="text-align:center">Crédito</td></tr>
                        <tr><td style="text-align:center; color: #28a745;"><b>{deb:,.2f}</b></td><td style="text-align:center; color: #dc3545;"><b>{cre:,.2f}</b></td></tr>
                    </table>
                    <div class="t-saldo">Saldo Final: {saldo_fin:,.2f}</div>
                </div>""", unsafe_allow_html=True)
    with tab_b:
        bal = df[mask_periodo].groupby(['grupo', 'nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0.0)
        st.table(bal)
else: st.info("Sem dados.")
