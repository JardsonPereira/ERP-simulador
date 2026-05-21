import streamlit as st
from supabase import create_client
from erp_functions import (
    mostrar_razonetes, mostrar_vendas_erp, mostrar_gestao
)

# Inicialização Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Navegação
menu = st.sidebar.radio("Navegação", ["🛒 ERP/Vendas", "📊 Razonetes", "⚙️ Gestão"])

# Roteamento centralizado
if menu == "🛒 ERP/Vendas":
    mostrar_vendas_erp(supabase, st.session_state.user.id)
elif menu == "📊 Razonetes":
    mostrar_razonetes(supabase, st.session_state.user.id)
elif menu == "⚙️ Gestão":
    mostrar_gestao(supabase, st.session_state.user.id)
