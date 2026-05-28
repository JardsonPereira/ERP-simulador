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
# Buscando dados
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()

# --- Conversão segura para DataFrame ---
df_lanc = pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame()
df_contas = pd.DataFrame(res_contas.data) if res_contas.data else pd.DataFrame()

if df_lanc.empty or df_contas.empty:
    st.warning("Dados insuficientes. Verifique se existem lançamentos e contas cadastradas.")
    st.stop()

# --- TRAVA DE SEGURANÇA: Verificação da coluna 'grupo' ---
if 'grupo' not in df_contas.columns:
    st.error("ERRO: A coluna 'grupo' não foi encontrada na tabela 'contas' do Supabase.")
    st.write("Colunas detectadas na tabela 'contas':", df_contas.columns.tolist())
    st.info("Ajuste o nome da coluna no banco de dados para 'grupo' ou altere o código.")
    st.stop()

# --- Merge Seguro ---
df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
df['grupo'] = df['grupo'].fillna('SEM GRUPO')
df['nome_conta'] = df['nome_conta'].fillna('Conta Desconhecida')

# --- Navegação ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Razonetes"

c1, c2, c3, c4 = st.columns(4)
if c1.button("📂 Plano de Contas"): st.session_state.view_mode = "Plano de Contas"
if c2.button("📊 Razonetes"): st.session_state.view_mode = "Razonetes"
if c3.button("📑 Balancete"): st.session_state.view_mode = "Balancete"
if c4.button("⚖️ Balanço"): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Exibição ---
if st.session_state.view_mode == "Plano de Contas":
    st.subheader("📂 Plano de Contas")
    st.dataframe(df_contas[['nome_conta', 'grupo']])

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes")
    for grupo in df['grupo'].unique():
        st.markdown(f"### Grupo: {grupo}")
        contas = df[df['grupo'] == grupo]['nome_conta'].unique()
        cols = st.columns(3)
        for i, conta in enumerate(contas):
            c_df = df[(df['grupo'] == grupo) & (df['nome_conta'] == conta)]
            deb = c_df[c_df['operacao'] == 'Débito']['valor'].sum()
            cred = c_df[c_df['operacao'] == 'Crédito']['valor'].sum()
            with cols[i % 3]:
                st.metric(conta, f"R$ {deb - cred:,.2f}")

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete")
    bal = df.groupby(['nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.dataframe(bal)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    # Cálculos agrupados
    ac = df[(df['grupo']=='Ativo Circulante') & (df['operacao']=='Débito')]['valor'].sum() - df[(df['grupo']=='Ativo Circulante') & (df['operacao']=='Crédito')]['valor'].sum()
    anc = df[(df['grupo']=='Ativo Não Circulante') & (df['operacao']=='Débito')]['valor'].sum() - df[(df['grupo']=='Ativo Não Circulante') & (df['operacao']=='Crédito')]['valor'].sum()
    pc = df[(df['grupo']=='Passivo Circulante') & (df['operacao']=='Crédito')]['valor'].sum() - df[(df['grupo']=='Passivo Circulante') & (df['operacao']=='Débito')]['valor'].sum()
    pnc = df[(df['grupo']=='Passivo Não Circulante') & (df['operacao']=='Crédito')]['valor'].sum() - df[(df['grupo']=='Passivo Não Circulante') & (df['operacao']=='Débito')]['valor'].sum()
    pl = df[(df['grupo']=='Patrimônio Líquido') & (df['operacao']=='Crédito')]['valor'].sum() - df[(df['grupo']=='Patrimônio Líquido') & (df['operacao']=='Débito')]['valor'].sum()
    res = df[df['grupo']=='Receitas']['valor'].sum() - df[df['grupo']=='Despesas']['valor'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total ATIVO", f"R$ {ac + anc:,.2f}")
    with col2:
        st.metric("Total PASSIVO + PL", f"R$ {pc + pnc + pl + res:,.2f}")
