import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()

# --- Verificação de Segurança (Para evitar o KeyError) ---
df_lanc = pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame()
df_contas = pd.DataFrame(res_contas.data) if res_contas.data else pd.DataFrame()

if df_lanc.empty or df_contas.empty:
    st.warning("Dados não carregados.")
    st.stop()

# Verificar se a coluna 'grupo' existe
if 'grupo' not in df_contas.columns:
    st.error(f"ERRO: A coluna 'grupo' não foi encontrada na tabela 'contas'.")
    st.write("Colunas encontradas:", df_contas.columns.tolist())
    st.info("Ajuste o nome da coluna no Supabase para 'grupo' ou altere no código.")
    st.stop()

# Merge Seguro
df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
df['grupo'] = df['grupo'].fillna('SEM GRUPO')
df['nome_conta'] = df['nome_conta'].fillna('Conta Desconhecida')

# --- Navegação ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Auditoria"

c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🔍 Auditoria"): st.session_state.view_mode = "Auditoria"
if c2.button("📂 Plano de Contas"): st.session_state.view_mode = "Plano de Contas"
if c3.button("📊 Razonetes"): st.session_state.view_mode = "Razonetes"
if c4.button("📑 Balancete"): st.session_state.view_mode = "Balancete"
if c5.button("⚖️ Balanço"): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Exibição ---

if st.session_state.view_mode == "Auditoria":
    st.subheader("🔍 Auditoria (Resolver Divergências)")
    sem_grupo = df[df['grupo'] == 'SEM GRUPO']
    if not sem_grupo.empty:
        st.warning(f"⚠️ Existem {len(sem_grupo)} lançamentos sem grupo definido! Isso causa a divergência.")
        st.dataframe(sem_grupo[['nome_conta', 'valor', 'justificativa', 'operacao']])
    else:
        st.success("✅ Todos os lançamentos estão agrupados corretamente.")

elif st.session_state.view_mode == "Plano de Contas":
    st.subheader("📂 Plano de Contas")
    st.dataframe(df_contas[['nome_conta', 'grupo']])

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes")
    for g in df['grupo'].unique():
        st.markdown(f"### Grupo: {g}")
        for conta in df[df['grupo'] == g]['nome_conta'].unique():
            c_df = df[(df['grupo'] == g) & (df['nome_conta'] == conta)]
            deb = c_df[c_df['operacao'] == 'Débito']['valor'].sum()
            cred = c_df[c_df['operacao'] == 'Crédito']['valor'].sum()
            st.write(f"**{conta}**: Débito: R$ {deb:,.2f} | Crédito: R$ {cred:,.2f} | Saldo: R$ {deb-cred:,.2f}")

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete")
    bal = df.groupby(['nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.dataframe(bal)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    
    # Cálculos manuais
    def get_saldo(g, n='D'):
        g_df = df[df['grupo'] == g]
        d = g_df[g_df['operacao'] == 'Débito']['valor'].sum()
        c = g_df[g_df['operacao'] == 'Crédito']['valor'].sum()
        return (d-c) if n=='D' else (c-d)

    ac = get_saldo('Ativo Circulante', 'D')
    anc = get_saldo('Ativo Não Circulante', 'D')
    pc = get_saldo('Passivo Circulante', 'C')
    pnc = get_saldo('Passivo Não Circulante', 'C')
    pl = get_saldo('Patrimônio Líquido', 'C')
    res = get_saldo('Receitas', 'C') - get_saldo('Despesas', 'D')
    sem_grupo = get_saldo('SEM GRUPO', 'D') # Valor que causa a divergência

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total ATIVO", f"R$ {ac + anc + sem_grupo:,.2f}")
        st.write(f"Ativo Circulante: {ac:,.2f}")
        st.write(f"Ativo Não Circulante: {anc:,.2f}")
        st.error(f"VALOR SEM GRUPO (Divergência): R$ {sem_grupo:,.2f}")
    with col2:
        st.metric("Total PASSIVO + PL", f"R$ {pc + pnc + pl + res:,.2f}")
        st.write(f"Passivo: {pc + pnc:,.2f}")
        st.write(f"PL + Resultado: {pl + res:,.2f}")
