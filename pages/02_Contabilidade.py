import streamlit as st
import pandas as pd
import sys
import os

# --- CONFIGURAÇÃO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

st.set_page_config(page_title="Contabilidade", layout="wide")

check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)

user = st.session_state.get('user')
if not user:
    st.warning("Usuário não autenticado.")
    st.stop()

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
        df_l = pd.DataFrame(res_lanc.data)
        df_c = pd.DataFrame(res_contas.data)
        df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
        df['grupo'] = df.get('grupo_lanc', df.get('grupo_conta', 'Outros'))
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        
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
                                st.markdown(f"**{conta}**<br>Saldo {tipo_saldo}: R$ {saldo:,.2f}", unsafe_allow_html=True)

        # --- TAB 2: BALANCETE ---
        with tab2:
            st.subheader("Balancete de Verificação")
            pivot = df_p.pivot_table(index='nome_conta', columns='operacao', values='valor', aggfunc='sum', fill_value=0)
            if 'Débito' not in pivot.columns: pivot['Débito'] = 0
            if 'Crédito' not in pivot.columns: pivot['Crédito'] = 0
            pivot['Saldo Devedor'] = pivot.apply(lambda x: x['Débito'] - x['Crédito'] if x['Débito'] > x['Crédito'] else 0, axis=1)
            pivot['Saldo Credor'] = pivot.apply(lambda x: x['Crédito'] - x['Débito'] if x['Crédito'] > x['Débito'] else 0, axis=1)
            st.dataframe(pivot.map(lambda x: f"R$ {x:,.2f}"), use_container_width=True)

        # --- TAB 3: BALANÇO PATRIMONIAL (LÓGICA CORRETA) ---
        with tab3:
            st.subheader("Balanço Patrimonial")
            
            # 1. Calculamos o saldo de cada conta individualmente
            balancete = df_p.groupby(['nome_conta', 'Categoria', 'operacao'])['valor'].sum().unstack(fill_value=0)
            balancete['Deb'] = balancete.get('Débito', 0)
            balancete['Cre'] = balancete.get('Crédito', 0)
            
            # 2. Definimos o Saldo Contábil com base na natureza do grupo
            # Se é Ativo, saldo = Débito - Crédito
            # Se é Passivo/PL, saldo = Crédito - Débito (natureza credora)
            def calcular_saldo_bp(row):
                cat = row.name[1]
                if 'Ativo' in cat: return row['Deb'] - row['Cre']
                if 'Passivo' in cat or 'Patrimônio' in cat: return row['Cre'] - row['Deb']
                return 0
            
            balancete['Saldo_BP'] = balancete.apply(calcular_saldo_bp, axis=1)
            
            # 3. Agrupamos por Categoria
            resumo_bp = balancete.groupby('Categoria')['Saldo_BP'].sum()
            
            ativo = resumo_bp[resumo_bp.index.str.contains('Ativo')].sum()
            passivo_pl = resumo_bp[resumo_bp.index.str.contains('Passivo|Patrimônio')].sum()
            
            # Exibição
            c1, c2 = st.columns(2)
            c1.metric("Total Ativo", f"R$ {ativo:,.2f}")
            c1.dataframe(resumo_bp[resumo_bp.index.str.contains('Ativo')], use_container_width=True)
            
            c2.metric("Total Passivo + PL", f"R$ {passivo_pl:,.2f}")
            c2.dataframe(resumo_bp[resumo_bp.index.str.contains('Passivo|Patrimônio')], use_container_width=True)
            
            if abs(ativo - passivo_pl) < 0.01:
                st.success("✅ Balanço Equilibrado!")
            else:
                st.error(f"⚠️ Diferença: R$ {(ativo - passivo_pl):,.2f}")
