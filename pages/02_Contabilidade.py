import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- 1. CARREGAMENTO BLINDADO ---
@st.cache_data(ttl=10) # Cache curto para forçar atualização
def carregar_dados_seguro():
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    
    df_lanc = pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame()
    df_contas = pd.DataFrame(res_contas.data) if res_contas.data else pd.DataFrame()
    
    if df_lanc.empty or df_contas.empty:
        return None
    
    # Padronização de tipos para o Merge funcionar
    df_lanc['conta_id'] = df_lanc['conta_id'].astype(int)
    df_contas['id'] = df_contas['id'].astype(int)
    
    # Merge forçado
    df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
    
    # Garantia de colunas obrigatórias
    if 'grupo' not in df.columns:
        df['grupo'] = 'SEM GRUPO'
    else:
        df['grupo'] = df['grupo'].fillna('SEM GRUPO')
        
    df['nome_conta'] = df['nome_conta'].fillna('Conta Desconhecida')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento']).dt.date
    
    return df

df = carregar_dados_seguro()

if df is None:
    st.warning("Dados não carregados. Verifique sua conexão ou se existem lançamentos.")
    st.stop()

# --- 2. FILTROS ---
st.sidebar.header("🗓️ Filtros")
data_inicio = st.sidebar.date_input("Data Início", value=date(2026, 1, 1))
data_fim = st.sidebar.date_input("Data Fim", value=date.today())

mask = (df['data_lancamento'] >= data_inicio) & (df['data_lancamento'] <= data_fim)
df_filtered = df.loc[mask]

# --- 3. NAVEGAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Auditoria"
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🔍 Auditoria"): st.session_state.view_mode = "Auditoria"
if c2.button("📂 Plano"): st.session_state.view_mode = "Plano"
if c3.button("📊 Razonetes"): st.session_state.view_mode = "Razonetes"
if c4.button("📑 Balancete"): st.session_state.view_mode = "Balancete"
if c5.button("⚖️ Balanço"): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- 4. EXIBIÇÃO ---
if st.session_state.view_mode == "Auditoria":
    st.subheader("🔍 Auditoria de Dados")
    # Debug visual rápido
    with st.expander("Ver colunas carregadas (Diagnóstico)"):
        st.write("Colunas no DataFrame:", df.columns.tolist())
    
    sem_grupo = df_filtered[df_filtered['grupo'] == 'SEM GRUPO']
    if not sem_grupo.empty:
        st.error(f"⚠️ {len(sem_grupo)} lançamentos no período não estão atribuídos a um grupo!")
        st.dataframe(sem_grupo[['nome_conta', 'valor', 'justificativa', 'data_lancamento']])
    else:
        st.success("✅ Tudo ok! Todos os lançamentos possuem grupo definido.")

elif st.session_state.view_mode == "Plano":
    st.dataframe(df[['nome_conta', 'grupo']].drop_duplicates())

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes")
    for g in df_filtered['grupo'].unique():
        st.markdown(f"### Grupo: {g}")
        for conta in df_filtered[df_filtered['grupo'] == g]['nome_conta'].unique():
            c_df = df_filtered[(df_filtered['grupo'] == g) & (df_filtered['nome_conta'] == conta)]
            deb = c_df[c_df['operacao'] == 'Débito']['valor'].sum()
            cred = c_df[c_df['operacao'] == 'Crédito']['valor'].sum()
            st.write(f"**{conta}**: D: R$ {deb:,.2f} | C: R$ {cred:,.2f} | Saldo: R$ {deb-cred:,.2f}")

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete")
    bal = df_filtered.groupby(['nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.dataframe(bal)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    def get_saldo(g, n='D'):
        g_df = df_filtered[df_filtered['grupo'] == g]
        d = g_df[g_df['operacao'] == 'Débito']['valor'].sum()
        c = g_df[g_df['operacao'] == 'Crédito']['valor'].sum()
        return (d-c) if n=='D' else (c-d)

    ac = get_saldo('Ativo Circulante', 'D')
    anc = get_saldo('Ativo Não Circulante', 'D')
    pc = get_saldo('Passivo Circulante', 'C')
    pnc = get_saldo('Passivo Não Circulante', 'C')
    pl = get_saldo('Patrimônio Líquido', 'C')
    res = get_saldo('Receitas', 'C') - get_saldo('Despesas', 'D')
    
    col1, col2 = st.columns(2)
    col1.metric("Total ATIVO", f"R$ {ac + anc:,.2f}")
    col2.metric("Total PASSIVO + PL", f"R$ {pc + pnc + pl + res:,.2f}")
    
    if abs((ac + anc) - (pc + pnc + pl + res)) > 0.01:
        st.error(f"⚠️ Divergência detectada! Verifique a aba Auditoria.")
