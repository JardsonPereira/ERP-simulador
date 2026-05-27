import streamlit as st
import pandas as pd
import sys
import os

# --- CONFIGURAÇÃO E AUTENTICAÇÃO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

user = check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)
user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)

st.title("📚 Contabilidade por Grupos")

# --- FUNÇÃO DE CLASSIFICAÇÃO ---
def classificar_conta(grupo):
    if not isinstance(grupo, str): return '8. Outros'
    g = grupo.lower()
    if 'ativo circulante' in g: return '1. Ativo Circulante'
    if 'ativo não circulante' in g: return '2. Ativo Não Circulante'
    if 'passivo circulante' in g: return '3. Passivo Circulante'
    if 'passivo não circulante' in g: return '4. Passivo Não Circulante'
    if 'patrimônio' in g or 'pl' in g: return '5. Patrimônio Líquido'
    if 'receita' in g: return '6. Receitas'
    if 'despesa' in g or 'custo' in g: return '7. Despesas'
    return '8. Outros'

if user_id:
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

    if res_lanc.data and res_contas.data:
        df = pd.DataFrame(res_lanc.data).merge(pd.DataFrame(res_contas.data), left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        if 'grupo' not in df.columns:
            df['grupo'] = df['grupo_lanc'] if 'grupo_lanc' in df.columns else df.get('grupo_conta', 'Outros')
        
        # Filtro
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Data Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Data Fim", value=df['data_lancamento'].max().date())
        df_p = df[(df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)].copy()
        df_p['valor'] = df_p['valor'].abs()
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
                                t_deb = d_c[d_c['operacao'] == 'Débito']['valor'].sum()
                                t_cre = d_c[d_c['operacao'] == 'Crédito']['valor'].sum()
                                saldo_final = abs(t_deb - t_cre)
                                tipo_saldo = "Devedor" if t_deb >= t_cre else "Credor"
                                
                                # Criar lista discreta de justificativas
                                justificativas = "<br>".join([f"• {j}" for j in d_c['justificativa'].unique()])
                                
                                st.markdown(f"""
                                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px; background-color: #f9f9f9;">
                                        <b>{conta}</b>
                                        <div style="border-top: 2px solid black; margin-top: 5px;"></div>
                                        <div style="display: flex; border-left: 2px solid black; height: 50px;">
                                            <div style="flex: 1; text-align: left; padding-left: 5px; font-size: 0.8em; color: #2e7d32;"><b>D</b>: {t_deb:,.2f}</div>
                                            <div style="flex: 1; text-align: right; padding-right: 5px; font-size: 0.8em; color: #c62828;"><b>C</b>: {t_cre:,.2f}</div>
                                        </div>
                                        <div style="border-top: 1px solid #eee; margin: 5px 0; padding-top: 5px; font-size: 0.75em; color: #555; text-align: left;">
                                            {justificativas}
                                        </div>
                                        <div style="border-top: 1px solid #ccc; padding-top: 5px; font-size: 0.9em; font-weight: bold;">
                                            Saldo {tipo_saldo}: R$ {saldo_final:,.2f}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

        with tab2:
            st.markdown("### Balancete de Verificação")
            pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
            if 'Débito' not in pivot.columns: pivot['Débito'] = 0
            if 'Crédito' not in pivot.columns: pivot['Crédito'] = 0
            pivot = pivot[['Débito', 'Crédito']]
            pivot['Saldo Devedor'] = (pivot['Débito'] - pivot['Crédito']).clip(lower=0)
            pivot['Saldo Credor'] = (pivot['Crédito'] - pivot['Débito']).clip(lower=0)
            pivot.loc['TOTAIS'] = pivot.sum()
            st.dataframe(pivot.style.format("R$ {:,.2f}"), use_container_width=True)

        with tab3:
            df_bal = df_p.groupby(['Categoria', 'nome_conta']).apply(lambda x: x[x['operacao'] == 'Débito']['valor'].sum() - x[x['operacao'] == 'Crédito']['valor'].sum()).reset_index(name='Saldo')
            resultado_exercicio = (df_bal[df_bal['Categoria'] == '6. Receitas']['Saldo'].sum() * -1) - df_bal[df_bal['Categoria'] == '7. Despesas']['Saldo'].sum()
            
            c_a, c_p = st.columns(2)
            with c_a:
                st.subheader("📋 ATIVO")
                total_ativo = 0
                for cat in [c for c in sorted(df_bal['Categoria'].unique()) if 'Ativo' in c]:
                    st.caption(f"**{cat[3:]}**")
                    df_a = df_bal[df_bal['Categoria'] == cat]
                    st.dataframe(df_a[['nome_conta', 'Saldo']], use_container_width=True, hide_index=True)
                    total_ativo += df_a['Saldo'].sum()
                st.metric("Total Ativo", f"R$ {total_ativo:,.2f}")
            with c_p:
                st.subheader("📋 PASSIVO E PL")
                total_ppl = 0
                for cat in [c for c in sorted(df_bal['Categoria'].unique()) if 'Passivo' in c]:
                    st.caption(f"**{cat[3:]}**")
                    df_p_ = df_bal[df_bal['Categoria'] == cat].copy()
                    df_p_['Saldo'] = df_p_['Saldo'] * -1
                    st.dataframe(df_p_[['nome_conta', 'Saldo']], use_container_width=True, hide_index=True)
                    total_ppl += df_p_['Saldo'].sum()
                st.caption("**Patrimônio Líquido**")
                df_pl = df_bal[df_bal['Categoria'] == '5. Patrimônio Líquido'].copy()
                df_pl['Saldo'] = df_pl['Saldo'] * -1
                df_pl = pd.concat([df_pl, pd.DataFrame({'nome_conta': ['Resultado do Exercício'], 'Saldo': [resultado_exercicio]})], ignore_index=True)
                st.dataframe(df_pl[['nome_conta', 'Saldo']], use_container_width=True, hide_index=True)
                total_ppl += df_pl['Saldo'].sum()
                st.metric("Total Passivo + PL", f"R$ {total_ppl:,.2f}")
    else:
        st.info("Nenhum lançamento encontrado.")
