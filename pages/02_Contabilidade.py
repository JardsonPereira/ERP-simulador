import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# 1. Buscar lançamentos e processar
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
if not res_lanc.data:
    st.info("Nenhum lançamento encontrado para gerar as demonstrações.")
    st.stop()

df = pd.DataFrame(res_lanc.data)

# 2. Lógica do Balancete (Consolidação)
# Agrupamos por conta e tipo para obter os saldos
def calcular_balancete(df):
    balancete = df.groupby(['conta_id', 'operacao'])['valor'].sum().unstack(fill_value=0)
    balancete['Saldo'] = balancete.get('Débito', 0) - balancete.get('Crédito', 0)
    return balancete

balancete = calcular_balancete(df)

# 3. Exibição dos Razonetes (Visualização em T)
st.subheader("📊 Razonetes (Livro Razão)")
for conta_id, group in df.groupby('conta_id'):
    with st.expander(f"Conta ID: {conta_id}"):
        col1, col2 = st.columns(2)
        deb = group[group['operacao'] == 'Débito']
        cred = group[group['operacao'] == 'Crédito']
        
        col1.write("**Débito**")
        col1.table(deb[['data_lancamento', 'valor', 'justificativa']])
        col2.write("**Crédito**")
        col2.table(cred[['data_lancamento', 'valor', 'justificativa']])
        st.write(f"**Saldo Final: R$ {deb['valor'].sum() - cred['valor'].sum():,.2f}**")

# 4. Balanço Patrimonial Simples
st.markdown("---")
st.subheader("⚖️ Balanço Patrimonial")

# Mapeamento simples de grupos para Balanço (deve ser refinado conforme sua lógica)
ativo = df[df['grupo'].isin(['Ativo Circulante', 'Ativo Não Circulante'])]
passivo = df[df['grupo'].isin(['Passivo Circulante', 'Passivo Não Circulante'])]
pl = df[df['grupo'].isin(['Patrimônio Líquido'])]

col_a, col_p = st.columns(2)
col_a.metric("Total Ativo", f"R$ {ativo['valor'].sum():,.2f}")
col_p.metric("Total Passivo + PL", f"R$ {(passivo['valor'].sum() + pl['valor'].sum()):,.2f}")

if abs(ativo['valor'].sum() - (passivo['valor'].sum() + pl['valor'].sum())) < 0.01:
    st.success("Balanço Equilibrado!")
else:
    st.error("Balanço Desequilibrado! Verifique as partidas dobradas.")
