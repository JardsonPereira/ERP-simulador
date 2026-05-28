import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# Inicializa o estado para alternar entre as visões
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Razonetes"

# --- Botões de Navegação ---
col1, col2, col3 = st.columns(3)
if col1.button("📊 Razonetes", use_container_width=True):
    st.session_state.view_mode = "Razonetes"
if col2.button("📑 Balancete", use_container_width=True):
    st.session_state.view_mode = "Balancete"
if col3.button("⚖️ Balanço Patrimonial", use_container_width=True):
    st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Lógica de Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
if not res_lanc.data:
    st.warning("Nenhum dado para exibir.")
    st.stop()

df = pd.DataFrame(res_lanc.data)

# --- Exibição Condicional ---
if st.session_state.view_mode == "Razonetes":
    st.subheader("Razonetes (Livro Razão)")
    # 
    for conta_id, group in df.groupby('conta_id'):
        with st.expander(f"Conta: {conta_id}"):
            c1, c2 = st.columns(2)
            c1.table(group[group['operacao'] == 'Débito'][['data_lancamento', 'valor', 'justificativa']])
            c2.table(group[group['operacao'] == 'Crédito'][['data_lancamento', 'valor', 'justificativa']])

elif st.session_state.view_mode == "Balancete":
    st.subheader("Balancete de Verificação")
    balancete = df.groupby(['conta_id', 'operacao'])['valor'].sum().unstack(fill_value=0)
    balancete['Saldo'] = balancete.get('Débito', 0) - balancete.get('Crédito', 0)
    st.dataframe(balancete, use_container_width=True)

elif st.session_state.view_mode == "Balanço":
    st.subheader("Balanço Patrimonial")
    ativo = df[df['grupo'].str.contains('Ativo', na=False)]['valor'].sum()
    passivo = df[df['grupo'].str.contains('Passivo', na=False)]['valor'].sum()
    pl = df[df['grupo'] == 'Patrimônio Líquido']['valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Ativo", f"R$ {ativo:,.2f}")
    m2.metric("Total Passivo", f"R$ {passivo:,.2f}")
    m3.metric("PL", f"R$ {pl:,.2f}")
    
    if abs(ativo - (passivo + pl)) < 0.01:
        st.success("Balanço Equilibrado!")
    else:
        st.error(f"Diferença: R$ {abs(ativo - (passivo + pl)):,.2f}")
