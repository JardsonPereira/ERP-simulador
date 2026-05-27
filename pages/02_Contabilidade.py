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
    # Busca os dados
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

    if res_lanc.data and res_contas.data:
        # Merge de Lançamentos e Contas
        df_lanc = pd.DataFrame(res_lanc.data)
        df_contas = pd.DataFrame(res_contas.data)
        
        df = df_lanc.merge(df_contas, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        
        # --- CORREÇÃO DO KEYERROR ('grupo') ---
        # Unifica as colunas de grupo, priorizando a que veio do lançamento
        if 'grupo' not in df.columns:
            if 'grupo_lanc' in df.columns:
                df['grupo'] = df['grupo_lanc']
            elif 'grupo_conta' in df.columns:
                df['grupo'] = df['grupo_conta']
            else:
                df['grupo'] = 'Outros'
        
        # Filtro de Data
        st.markdown("---")
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Data Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Data Fim", value=df['data_lancamento'].max().date())
        
        df_p = df[(df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)].copy()
        
        if not df_p.empty:
            df_p['valor'] = df_p['valor'].abs()
            df_p['Categoria'] = df_p['grupo'].apply(classificar_conta)

            tab1, tab2, tab3 = st.tabs(["Razonetes (T)", "Balancete", "Balanço Patrimonial"])
            
            # --- TAB 1: RAZONETES ---
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
                                    
                                    # Gera HTML para Débitos e Créditos com justificativa abaixo
                                    deb_list = "".join([f"<div style='margin-bottom:10px; border-bottom:1px solid #eee;'><b>R$ {r.valor:,.2f}</b><br><small style='color:#666;'>{r.justificativa}</small></div>" for _, r in d_c[d_c['operacao'] == 'Débito'].iterrows()])
                                    cre_list = "".join([f"<div style='margin-bottom:10px; border-bottom:1px solid #eee;'><b>R$ {r.valor:,.2f}</b><br><small style='color:#666;'>{r.justificativa}</small></div>" for _, r in d_c[d_c['operacao'] == 'Crédito'].iterrows()])
                                    
                                    st.markdown(f"""
                                        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #fafafa; margin-bottom: 10px;">
                                            <div style="text-align: center; font-weight: bold;">{conta}</div>
                                            <div style="border-top: 2px solid #333; margin: 5px 0;"></div>
                                            <div style="display: flex; border-left: 2px solid #333; min-height: 120px;">
                                                <div style="flex: 1; text-align: left; padding: 5px; border-right: 1px solid #ddd;">
                                                    <div style="color: #2e7d32; margin-bottom: 5px; font-size: 0.8em;"><b>DÉBITOS</b></div>
                                                    {deb_list if deb_list else '<small>---</small>'}
                                                </div>
                                                <div style="flex: 1; text-align: right; padding: 5px;">
                                                    <div style="color: #c62828; margin-bottom: 5px; font-size: 0.8em;"><b>CRÉDITOS</b></div>
                                                    {cre_list if cre_list else '<small>---</small>'}
                                                </div>
                                            </div>
                                            <div style="border-top: 1px solid #ccc; padding-top: 5px; text-align: center; font-weight: bold;">
                                                Saldo {tipo_saldo}: R$ {saldo_final:,.2f}
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)

            # --- TAB 2: BALANCETE (Usa st.dataframe, não data_editor) ---
            with tab2:
                st.markdown("### Balancete de Verificação")
                pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
                pivot = pivot.reindex(columns=['Débito', 'Crédito'], fill_value=0)
                pivot['Saldo Devedor'] = (pivot['Débito'] - pivot['Crédito']).clip(lower=0)
                pivot['Saldo Credor'] = (pivot['Crédito'] - pivot['Débito']).clip(lower=0)
                pivot.loc['TOTAIS'] = pivot.sum()
                
                df_display = pivot.reset_index().rename(columns={'nome_conta': 'Conta'})
                st.dataframe(df_display.style.format({c: 'R$ {:,.2f}' for c in ['Débito', 'Crédito', 'Saldo Devedor', 'Saldo Credor']}), use_container_width=True, hide_index=True)

            # --- TAB 3: BALANÇO ---
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
            st.info("Nenhum lançamento no período selecionado.")
    else:
        st.info("Nenhum lançamento encontrado no banco de dados.")
