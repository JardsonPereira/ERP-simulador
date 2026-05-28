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

# --- 1. CARREGAMENTO E MERGE CORRETO ---
@st.cache_data(ttl=60)
def carregar_dados():
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    
    df_lanc = pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame()
    df_contas = pd.DataFrame(res_contas.data) if res_contas.data else pd.DataFrame()
    
    if df_lanc.empty or df_contas.empty: return None, None
    
    # A MÁGICA: O Grupo vem da tabela de Contas e é unido aos Lançamentos pelo conta_id
    df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
    
    # Tratamento de segurança
    df['grupo'] = df['grupo'].fillna('SEM GRUPO')
    df['nome_conta'] = df['nome_conta'].fillna('Conta Desconhecida')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento']).dt.date
    return df, df_contas

df, df_contas = carregar_dados()

if df is None:
    st.warning("Dados não carregados.")
    st.stop()

# --- 2. CSS RESTAURADO ---
st.markdown("""
    <style>
    .t-wrapper { border: 1px solid #ccc; padding: 10px; margin-bottom: 15px; border-radius: 8px; background: #ffffff; }
    .t-header { background: #333; color: white; text-align: center; font-weight: bold; padding: 5px; border-radius: 4px; margin-bottom: 5px; }
    .total-deb { color: green; font-size: 1em; font-weight: bold; text-align: right; }
    .total-cred { color: red; font-size: 1em; font-weight: bold; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- 3. FILTROS ---
st.sidebar.header("🗓️ Filtros")
data_inicio = st.sidebar.date_input("Data Início", value=date(2026, 1, 1))
data_fim = st.sidebar.date_input("Data Fim", value=date.today())
mask = (df['data_lancamento'] >= data_inicio) & (df['data_lancamento'] <= data_fim)
df_filtered = df.loc[mask]

# --- 4. NAVEGAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Auditoria"
c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🔍 Auditoria"): st.session_state.view_mode = "Auditoria"
if c2.button("📂 Plano"): st.session_state.view_mode = "Plano"
if c3.button("📊 Razonetes"): st.session_state.view_mode = "Razonetes"
if c4.button("📑 Balancete"): st.session_state.view_mode = "Balancete"
if c5.button("⚖️ Balanço"): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- 5. EXIBIÇÃO (RESTAURADA) ---
if st.session_state.view_mode == "Auditoria":
    st.subheader("🔍 Auditoria de Divergências")
    sem_grupo = df_filtered[df_filtered['grupo'] == 'SEM GRUPO']
    if not sem_grupo.empty:
        st.error(f"⚠️ {len(sem_grupo)} lançamentos sem grupo no período! A divergência de R$ 500 está aqui:")
        st.dataframe(sem_grupo[['nome_conta', 'valor', 'justificativa', 'data_lancamento']])
    else:
        st.success("✅ Tudo ok! Todos os lançamentos no período possuem grupo.")

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes")
    config = {"data_lancamento": st.column_config.DateColumn("Data"), "valor": st.column_config.NumberColumn("Valor", format="R$ %.2f")}
    for g in df_filtered['grupo'].unique():
        st.markdown(f"#### 📂 Grupo: {g}")
        contas = df_filtered[df_filtered['grupo'] == g]['nome_conta'].unique()
        cols = st.columns(2)
        for i, conta in enumerate(contas):
            c_df = df_filtered[(df_filtered['grupo'] == g) & (df_filtered['nome_conta'] == conta)]
            deb = c_df[c_df['operacao'] == 'Débito'].copy()
            cred = c_df[c_df['operacao'] == 'Crédito'].copy()
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                c_d, c_c = st.columns(2)
                with c_d:
                    st.markdown("<p style='color:green; font-weight:bold;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], height=120, use_container_width=True, column_config=config)
                    st.markdown(f"<p class='total-deb'>Total D: R$ {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                with c_c:
                    st.markdown("<p style='color:red; font-weight:bold;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], height=120, use_container_width=True, column_config=config)
                    st.markdown(f"<p class='total-cred'>Total C: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df_filtered.groupby(['nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.metric("Diferença Total", f"R$ {bal.get('Débito', 0).sum() - bal.get('Crédito', 0).sum():,.2f}")
    st.dataframe(bal, use_container_width=True)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    def get_saldo(g, n='D'):
        g_df = df_filtered[df_filtered['grupo'] == g]
        d = g_df[g_df['operacao'] == 'Débito']['valor'].sum()
        c = g_df[g_df['operacao'] == 'Crédito']['valor'].sum()
        return (d-c) if n=='D' else (c-d)
    
    ac, anc = get_saldo('Ativo Circulante', 'D'), get_saldo('Ativo Não Circulante', 'D')
    pc, pnc = get_saldo('Passivo Circulante', 'C'), get_saldo('Passivo Não Circulante', 'C')
    pl, res = get_saldo('Patrimônio Líquido', 'C'), (get_saldo('Receitas', 'C') - get_saldo('Despesas', 'D'))
    
    col1, col2 = st.columns(2)
    col1.metric("Total ATIVO", f"R$ {ac + anc:,.2f}")
    col2.metric("Total PASSIVO + PL", f"R$ {pc + pnc + pl + res:,.2f}")
    
    if abs((ac + anc) - (pc + pnc + pl + res)) > 0.01:
        st.error(f"⚠️ Divergência de R$ {(ac + anc) - (pc + pnc + pl + res):,.2f}. Verifique a aba Auditoria.")
