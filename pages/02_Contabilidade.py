import streamlit as st
import pandas as pd
import sys
import os

# --- CONFIGURAÇÃO E AUTENTICAÇÃO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

st.set_page_config(page_title="Contabilidade", layout="wide")

check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)

user = st.session_state.user
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
    if 'encargo' in g: return '7. Despesas' 
    return '8. Outros'

if user_id:
    # Busca os dados
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

    if res_lanc.data and res_contas.data:
        df_l = pd.DataFrame(res_lanc.data)
        df_c = pd.DataFrame(res_contas.data)
        
        # Merge seguro
        df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
        
        # Unificação da coluna grupo
        df['grupo'] = df.get('grupo_lanc', df.get('grupo_conta', 'Outros'))
        
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
        # Filtro de Data
        st.markdown("---")
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Data Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Data Fim", value=df['data_lancamento'].max().date())
        
        df_p = df[(df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)].copy()
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
                                saldo = abs(t_deb - t_cre)
                                tipo_saldo = "Devedor" if t_deb >= t_cre else "Credor"
                                
                                deb_list = "".join([f"<div style='border-bottom:1px solid #eee; margin-bottom:5px;'><small>R$ {r.valor:,.2f}</small><br><b style='font-size:0.8em;'>{r.justificativa}</b></div>" for _, r in d_c[d_c['operacao'] == 'Débito'].iterrows()])
                                cre_list = "".join([f"<div style='border-bottom:1px solid #eee; margin-bottom:5px;'><small>R$ {r.valor:,.2f}</small><br><b style='font-size:0.8em;'>{r.justificativa}</b></div>" for _, r in d_c[d_c['operacao'] == 'Crédito'].iterrows()])
                                
                                st.markdown(f"""
                                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #fafafa; margin-bottom:10px;">
                                        <div style="text-align: center; font-weight: bold;">{conta}</div>
                                        <hr style="margin:5px 0;">
                                        <div style="display: flex;">
                                            <div style="flex: 1; padding: 5px; border-right: 1px solid #ddd;"><div style="font-size:0.7em; color:green;">DÉBITO</div>{deb_list}</div>
                                            <div style="flex: 1; padding: 5px; text-align: right;"><div style="font-size:0.7em; color:red;">CRÉDITO</div>{cre_list}</div>
                                        </div>
                                        <div style="text-align:center; margin-top:5px; font-weight:bold; font-size:0.9em;">Saldo {tipo_saldo}: R$ {saldo:,.2f}</div>
                                    </div>
                                """, unsafe_allow_html=True)

        # --- TAB 2: BALANCETE ---
        with tab2:
            st.subheader("Balancete de Verificação")
            pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
            
            if 'Débito' not in pivot.columns: pivot['Débito'] = 0
            if 'Crédito' not in pivot.columns: pivot['Crédito'] = 0
            pivot['Saldo'] = pivot['Débito'] - pivot['Crédito']
            
            # Métricas Totais
            total_deb = pivot['Débito'].sum()
            total_cre = pivot['Crédito'].sum()
            
            col_m1, col_m2 = st.columns(2)
            col_m1.metric("Total Débitos", f"R$ {total_deb:,.2f}")
            col_m2.metric("Total Créditos", f"R$ {total_cre:,.2f}")
            
            # Exibição Formatada
            pivot_display = pivot.copy()
            pivot_display['Débito'] = pivot_display['Débito'].apply(lambda x: f"R$ {x:,.2f}")
            pivot_display['Crédito'] = pivot_display['Crédito'].apply(lambda x: f"R$ {x:,.2f}")
            pivot_display['Saldo'] = pivot_display['Saldo'].apply(lambda x: f"R$ {x:,.2f}")
            
            st.dataframe(pivot_display, use_container_width=True)
            
            if abs(total_deb - total_cre) < 0.01:
                st.success("✅ Balancete equilibrado: A soma de Débitos e Créditos é igual.")
            else:
                st.error(f"⚠️ Balancete desequilibrado! Diferença: R$ {(total_deb - total_cre):,.2f}")

        # --- TAB 3: BALANÇO PATRIMONIAL ---
        with tab3:
            st.subheader("Balanço Patrimonial (Ativo = Passivo + PL)")
            
            ativo = df_p[df_p['Categoria'].isin(['1. Ativo Circulante', '2. Ativo Não Circulante'])]['valor'].sum()
            passivo = df_p[df_p['Categoria'].isin(['3. Passivo Circulante', '4. Passivo Não Circulante'])]['valor'].sum()
            pl = df_p[df_p['Categoria'] == '5. Patrimônio Líquido']['valor'].sum()
            
            c_left, c_right = st.columns(2)
            with c_left:
                st.metric("Total Ativo", f"R$ {ativo:,.2f}")
                st.dataframe(df_p[df_p['Categoria'].str.contains('Ativo')].groupby('Categoria')['valor'].sum(), use_container_width=True)
            with c_right:
                st.metric("Total Passivo + PL", f"R$ {(passivo + pl):,.2f}")
                st.dataframe(df_p[df_p['Categoria'].str.contains('Passivo|Patrimônio')].groupby('Categoria')['valor'].sum(), use_container_width=True)
            
            if abs(ativo - (passivo + pl)) < 0.01:
                st.success("✅ Balanço Equilibrado!")
            else:
                st.error(f"⚠️ Balanço Desequilibrado: Diferença de R$ {(ativo - (passivo + pl)):,.2f}")

    else:
        st.info("Nenhum lançamento encontrado no período.")
