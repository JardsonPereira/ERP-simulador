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

# --- Tratamento de Erros e Merge ---
df_lanc = pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame()
df_contas = pd.DataFrame(res_contas.data) if res_contas.data else pd.DataFrame()

if df_lanc.empty or df_contas.empty:
    st.warning("Dados insuficientes para carregar a contabilidade.")
    st.stop()

# Verificação crítica: A coluna 'grupo' existe?
if 'grupo' not in df_contas.columns:
    st.error(f"Erro: A coluna 'grupo' não foi encontrada na tabela 'contas'. Colunas presentes: {df_contas.columns.tolist()}")
    st.stop()

# Merge
df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
df['grupo'] = df['grupo'].fillna('Sem Grupo')
df['nome_conta'] = df['nome_conta'].fillna('Conta Desconhecida')

# --- Navegação ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Razonetes"

c1, c2, c3, c4 = st.columns(4)
if c1.button("📂 Plano de Contas"): st.session_state.view_mode = "Plano de Contas"
if c2.button("📊 Razonetes"): st.session_state.view_mode = "Razonetes"
if c3.button("📑 Balancete"): st.session_state.view_mode = "Balancete"
if c4.button("⚖️ Balanço"): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Funções Auxiliares ---
def get_saldo_grupo(grupo, nature='D'):
    # nature='D' (Ativo/Despesa), 'C' (Passivo/PL/Receita)
    g_df = df[df['grupo'] == grupo]
    d = g_df[g_df['operacao'] == 'Débito']['valor'].sum()
    c = g_df[g_df['operacao'] == 'Crédito']['valor'].sum()
    return (d - c) if nature == 'D' else (c - d)

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
            saldo = c_df[c_df['operacao'] == 'Débito']['valor'].sum() - c_df[c_df['operacao'] == 'Crédito']['valor'].sum()
            with cols[i % 3]:
                st.metric(conta, f"R$ {saldo:,.2f}")

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete")
    bal = df.groupby(['nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.dataframe(bal, use_container_width=True)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial (Auditoria de Valores)")
    
    # Cálculo manual para facilitar a depuração da divergência
    ac = get_saldo_grupo('Ativo Circulante', 'D')
    anc = get_saldo_grupo('Ativo Não Circulante', 'D')
    pc = get_saldo_grupo('Passivo Circulante', 'C')
    pnc = get_saldo_grupo('Passivo Não Circulante', 'C')
    pl = get_saldo_grupo('Patrimônio Líquido', 'C')
    
    # Resultado (Receitas - Despesas)
    rec = get_saldo_grupo('Receitas', 'C')
    desp = get_saldo_grupo('Despesas', 'D')
    res = rec - desp
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ATIVO")
        st.write(f"Ativo Circulante: R$ {ac:,.2f}")
        st.write(f"Ativo Não Circulante: R$ {anc:,.2f}")
        st.metric("TOTAL ATIVO", f"R$ {ac + anc:,.2f}")
        
    with col2:
        st.markdown("### PASSIVO + PL")
        st.write(f"Passivo Circulante: R$ {pc:,.2f}")
        st.write(f"Passivo Não Circulante: R$ {pnc:,.2f}")
        st.write(f"PL: R$ {pl:,.2f}")
        st.write(f"Resultado do Exercício: R$ {res:,.2f}")
        st.metric("TOTAL PASSIVO + PL", f"R$ {pc + pnc + pl + res:,.2f}")
    
    # Alerta de divergência detalhado
    diferenca = (ac + anc) - (pc + pnc + pl + res)
    if abs(diferenca) > 0.01:
        st.error(f"⚠️ DIVERGÊNCIA DETECTADA: R$ {diferenca:,.2f}")
        st.info("Verifique se existem lançamentos com contas que NÃO possuem grupo ou que estão com o grupo escrito incorretamente.")
