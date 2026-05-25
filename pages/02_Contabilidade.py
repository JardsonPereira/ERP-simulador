import streamlit as st

# Proteção de página: redireciona se não estiver logado
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Acesso não autorizado. Por favor, faça o login.")
    st.stop()  # Impede que o restante do código seja carregado

# --- Seu código existente da página começa aqui ---
import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Contabilidade por Grupos")

# Função de Classificação Hierárquica
def classificar_conta(grupo):
    g = grupo.lower()
    if 'ativo circulante' in g: return '1. Ativo Circulante'
    if 'ativo não circulante' in g: return '2. Ativo Não Circulante'
    if 'passivo circulante' in g: return '3. Passivo Circulante'
    if 'passivo não circulante' in g: return '4. Passivo Não Circulante'
    if 'patrimonio' in g or 'pl' in g: return '5. Patrimônio Líquido'
    return '6. Outros'

lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Filtro de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    df_p = df[(df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)].copy()
    
    df_p['Categoria'] = df_p['grupo'].apply(classificar_conta)

    tab1, tab2, tab3 = st.tabs(["Razonetes (T)", "Balancete", "Balanço Patrimonial"])
    
    with tab1:
        for cat in sorted(df_p['Categoria'].unique()):
            st.subheader(f"📁 {cat}")
            contas_cat = sorted(df_p[df_p['Categoria'] == cat]['nome_conta'].unique())
            for i in range(0, len(contas_cat), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(contas_cat):
                        conta = contas_cat[i+j]
                        with col:
                            d_c = df_p[df_p['nome_conta'] == conta]
                            t_deb, t_cre = d_c[d_c['operacao'] == 'DEBITO']['valor'].sum(), d_c[d_c['operacao'] == 'CREDITO']['valor'].sum()
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
        # Balancete agrupado por Categoria
        for cat in sorted(df_p['Categoria'].unique()):
            if cat == '6. Outros': continue
            st.markdown(f"### {cat}")
            df_cat = df_p[df_p['Categoria'] == cat]
            pivot = df_cat.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
            pivot = pivot.reindex(columns=['DEBITO', 'CREDITO'], fill_value=0)
            pivot['Saldo Devedor'] = (pivot['DEBITO'] - pivot['CREDITO']).clip(lower=0)
            pivot['Saldo Credor'] = (pivot['CREDITO'] - pivot['DEBITO']).clip(lower=0)
            st.dataframe(pivot.style.format("R$ {:,.2f}"), use_container_width=True)

    with tab3:
        # Lógica de Balanço Patrimonial (Ativo vs Passivo+PL)
        df_bal = df_p[df_p['Categoria'] != '6. Outros'].groupby(['Categoria', 'nome_conta']).apply(
            lambda x: x[x['operacao'] == 'DEBITO']['valor'].sum() - x[x['operacao'] == 'CREDITO']['valor'].sum()
        ).reset_index(name='Saldo')

        col_a, col_p = st.columns(2)
        with col_a:
            st.subheader("📋 ATIVO")
            for cat in [c for c in sorted(df_bal['Categoria'].unique()) if 'Ativo' in c]:
                st.caption(f"**{cat}**")
                st.dataframe(df_bal[df_bal['Categoria'] == cat][['nome_conta', 'Saldo']], use_container_width=True, hide_index=True)
            total_ativo = df_bal[df_bal['Categoria'].str.contains('Ativo')]['Saldo'].sum()
            st.metric("Total Ativo", f"R$ {total_ativo:,.2f}")

        with col_p:
            st.subheader("📋 PASSIVO E PL")
            for cat in [c for c in sorted(df_bal['Categoria'].unique()) if 'Passivo' in c or 'Patrimônio' in c]:
                st.caption(f"**{cat}**")
                df_ppl = df_bal[df_bal['Categoria'] == cat].copy()
                df_ppl['Saldo'] = df_ppl['Saldo'].abs()
                st.dataframe(df_ppl[['nome_conta', 'Saldo']], use_container_width=True, hide_index=True)
            total_passivo_pl = df_bal[df_bal['Categoria'].str.contains('Passivo|Patrimônio')]['Saldo'].abs().sum()
            st.metric("Total Passivo + PL", f"R$ {total_passivo_pl:,.2f}")

        st.divider()
        if abs(total_ativo - total_passivo_pl) < 0.01:
            st.success("Balanço Patrimonial Equilibrado ✅")
        else:
            st.error("Diferença no Balanço! Verifique os lançamentos ⚠️")

else:
    st.info("Sem dados para exibir.")
