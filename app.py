import streamlit as st
from erp_functions import (
    mostrar_razonetes, mostrar_balancete, mostrar_dre, 
    mostrar_fluxo_caixa, mostrar_vendas_erp, mostrar_gestao
)
from supabase import create_client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Didático Integrado", layout="wide")

# Inicialização Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Erro na configuração do Supabase. Verifique suas Secrets.")
    st.stop()

# --- ESTADOS DO SISTEMA ---
if 'menu_opcao' not in st.session_state:
    st.session_state.menu_opcao = "🛒 ERP/Vendas"

# --- NAVEGAÇÃO ---
st.sidebar.title("🏢 Menu ERP")
opcoes_menu = [
    "🛒 ERP/Vendas", "📊 Razonetes", "🧾 Balancete", 
    "📈 DRE", "💸 Fluxo de Caixa", "⚙️ Gestão"
]
menu_selecionado = st.sidebar.radio("Escolha o Módulo:", opcoes_menu)
st.session_state.menu_opcao = menu_selecionado

st.divider()

# --- ROTEAMENTO ---
# Aqui passamos a instância do supabase para as funções
if st.session_state.menu_opcao == "🛒 ERP/Vendas":
    mostrar_vendas_erp(supabase)
elif st.session_state.menu_opcao == "📊 Razonetes":
    mostrar_razonetes(supabase)
elif st.session_state.menu_opcao == "🧾 Balancete":
    mostrar_balancete(supabase)
elif st.session_state.menu_opcao == "📈 DRE":
    mostrar_dre(supabase)
elif st.session_state.menu_opcao == "💸 Fluxo de Caixa":
    mostrar_fluxo_caixa(supabase)
elif st.session_state.menu_opcao == "⚙️ Gestão":
    mostrar_gestao(supabase)
