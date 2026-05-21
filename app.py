import streamlit as st
from supabase import create_client
from erp_functions import (
    mostrar_razonetes, mostrar_balancete, mostrar_dre, 
    mostrar_fluxo_caixa, mostrar_vendas_erp, mostrar_gestao
)

# Configuração
st.set_page_config(layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Menu
menu = st.sidebar.radio("Navegação", [
    "🛒 ERP/Vendas", "📊 Razonetes", "🧾 Balancete", 
    "📈 DRE", "💸 Fluxo de Caixa", "⚙️ Gestão"
])

# Roteamento Padronizado (todas recebem apenas 'supabase')
if menu == "🛒 ERP/Vendas": mostrar_vendas_erp(supabase)
elif menu == "📊 Razonetes": mostrar_razonetes(supabase)
elif menu == "🧾 Balancete": mostrar_balancete(supabase)
elif menu == "📈 DRE": mostrar_dre(supabase)
elif menu == "💸 Fluxo de Caixa": mostrar_fluxo_caixa(supabase)
elif menu == "⚙️ Gestão": mostrar_gestao(supabase)
