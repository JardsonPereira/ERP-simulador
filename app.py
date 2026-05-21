import streamlit as st
from supabase import create_client
from erp_functions import mostrar_vendas_erp, mostrar_gestao

# Inicialização
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

st.sidebar.title("ERP Didático")
menu = st.sidebar.radio("Navegação", ["🛒 ERP/Vendas", "⚙️ Gestão"])

if st.session_state.user:
    u_id = st.session_state.user.id
    if menu == "🛒 ERP/Vendas":
        mostrar_vendas_erp(supabase, u_id)
    elif menu == "⚙️ Gestão":
        mostrar_gestao(supabase, u_id)
else:
    st.warning("Efetue o login para acessar o ERP.")
