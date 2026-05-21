import streamlit as st
from erp_functions import mostrar_razonetes, mostrar_balancete, mostrar_dre, mostrar_fluxo_caixa, mostrar_vendas_erp, mostrar_gestao

# ... (Mantenha aqui seu código de CONFIGURAÇÃO, ESTADOS e CONEXÃO SUPABASE)

# --- NAVEGAÇÃO ---
# Mantendo sua estrutura de botões
col_nav = st.columns(6) # Adicionamos uma coluna para o novo menu ERP
opcoes_menu = ["📊 Razonetes", "🧾 Balancete", "📈 DRE", "💸 Fluxo de Caixa", "🛒 ERP/Vendas", "⚙️ Gestão"]
for i, op in enumerate(opcoes_menu):
    if col_nav[i].button(op, use_container_width=True): st.session_state.menu_opcao = op

st.divider()

# --- ROTEAMENTO POR FUNÇÕES ---
if st.session_state.menu_opcao == "📊 Razonetes":
    mostrar_razonetes(supabase, st.session_state.user.id, id_usuario_filtrado)
elif st.session_state.menu_opcao == "🧾 Balancete":
    mostrar_balancete(supabase, id_usuario_filtrado)
elif st.session_state.menu_opcao == "📈 DRE":
    mostrar_dre(df_periodo)
elif st.session_state.menu_opcao == "💸 Fluxo de Caixa":
    mostrar_fluxo_caixa(df_periodo, df_balanco)
elif st.session_state.menu_opcao == "🛒 ERP/Vendas":
    mostrar_vendas_erp(supabase)
elif st.session_state.menu_opcao == "⚙️ Gestão":
    mostrar_gestao(supabase, id_usuario_filtrado)
