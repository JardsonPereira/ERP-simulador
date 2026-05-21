import streamlit as st
from supabase import create_client
from erp_functions import (
    mostrar_razonetes, mostrar_balancete, mostrar_dre, 
    mostrar_fluxo_caixa, mostrar_vendas_erp, mostrar_gestao
)

# Inicialização
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Garantir que o user esteja no session_state antes de qualquer coisa
if 'user' not in st.session_state: st.session_state.user = None

# Menu lateral
menu = st.sidebar.radio("Navegação", [
    "🛒 ERP/Vendas", "📊 Razonetes", "🧾 Balancete", 
    "📈 DRE", "💸 Fluxo de Caixa", "⚙️ Gestão"
])

# Roteamento seguro
if st.session_state.user:
    u_id = st.session_state.user.id
    if menu == "🛒 ERP/Vendas": mostrar_vendas_erp(supabase, u_id)
    elif menu == "📊 Razonetes": mostrar_razonetes(supabase, u_id)
    elif menu == "⚙️ Gestão": mostrar_gestao(supabase, u_id)
    # ... adicione as outras conforme necessário
else:
    st.warning("Faça login para acessar os módulos do ERP.")
