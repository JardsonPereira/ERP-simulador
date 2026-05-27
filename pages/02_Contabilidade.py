import streamlit as st
import pandas as pd
import sys
import os

# --- CONFIGURAÇÃO E AUTENTICAÇÃO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)
# Recupera ID do usuário de forma robusta
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
    if 'encargo' in g: return '7. Despesas'  # Encargos Financeiros classificados como Despesa
    return '8. Outros'

if user_id:
    # Busca dados
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

    if res_lanc.data and res_contas.data:
        df_l = pd.DataFrame(res_lanc.data)
        df_c = pd.DataFrame(res_contas.data)
        
        # Merge Seguro
        df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
        
        # Correção do KeyError 'grupo' (Garante a existência da coluna unificada)
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
                                
                                deb_list = "".join([f"<div style='border-bottom:1px solid #eee; margin-bottom:5px;'><b>R$ {r.valor:,.2f}</b><br><small style='color:#666;'>{r.justificativa}</small></div>" for _, r in d_c[d_c['operacao'] == 'Débito'].iterrows()])
                                cre_list = "".join([f"<div style='border-bottom:1px solid #eee; margin-bottom:5px;'><b>R$ {r.valor:,.2f}</b><br><small style='color:#666;'>{r.justificativa}</small></div>" for _, r in d_c[d_c['operacao'] == 'Crédito'].iterrows()])
                                
                                st.markdown(f"""
                                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #fafafa;">
                                        <div style="text-align: center; font-weight: bold;">{conta}</div>
                                        <hr style="margin:5px 0;">
                                        <div style="display: flex;">
                                            <div style="flex: 1; padding: 5px; border-right: 1px solid #ddd;">
                                                <div style="font-size:0.7em; color:green;">DÉBITO</div>{deb_list}
                                            </div>
                                            <div style="flex: 1; padding: 5px; text-align: right;">
                                                <div style="font-size:0.7em; color:red;">CRÉDITO</div>{cre_list}
                                            </div>
                                        </div>
                                        <div style="text-align:center; margin-top:10px; font-weight:bold;">Saldo {tipo_saldo}: R$ {saldo:,.2f}</div>
                                    </div>
                                """, unsafe_allow_html=True)

        # --- TAB 2: BALANCETE ---
        with tab2:
            pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
            if 'Débito' not in pivot.columns: pivot['Débito'] = 0
            if 'Crédito' not in pivot.columns: pivot['Crédito'] = 0
            pivot['Saldo'] = pivot['Débito'] - pivot['Crédito']
            st.dataframe(pivot, use_container_width=True)

        # --- TAB 3: BALANÇO ---
        with tab3:
            st.write("Visão sintética do patrimônio calculada a partir dos saldos das contas.")
            df_bal = df_p.groupby('Categoria')['valor'].sum().reset_index()
            st.dataframe(df_bal, use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado.")
