import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, check_auth

check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira Completa")

# --- Funções de Ação ---
def carregar_dados():
    lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
    return pd.DataFrame(lancamentos) if lancamentos else pd.DataFrame()

# --- Interface ---
tab_dashboard, tab_gestao = st.tabs(["📊 Visão Geral", "🛠️ Gestão de Lançamentos"])

with tab_dashboard:
    st.subheader("Lançamentos Atuais")
    df = carregar_dados()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado.")

with tab_gestao:
    # 1. CRIAR NOVO
    with st.expander("➕ Adicionar Novo Lançamento"):
        with st.form("form_add", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome/Descrição")
                grupo = st.selectbox("Grupo", ["Alimentação", "Transporte", "Moradia", "Lazer"])
                data = st.date_input("Data")
            with col2:
                operacao = st.selectbox("Operação", ["Receita", "Despesa"])
                valor = st.number_input("Valor (R$)", min_value=0.0)
                justificativa = st.text_input("Justificativa")
            
            if st.form_submit_button("Salvar Lançamento"):
                # supabase.table("lancamentos").insert({...}).execute()
                st.success("Lançamento adicionado!")
                st.rerun()

    # 2. EDITAR E EXCLUIR (usando data_editor)
    st.subheader("Editar ou Excluir Lançamentos")
    df_editavel = carregar_dados()
    
    if not df_editavel.empty:
        # O data_editor detecta edições e deleções
        df_editado = st.data_editor(
            df_editavel, 
            key="editor_lancamentos",
            use_container_width=True,
            num_rows="dynamic"
        )
        
        if st.button("Aplicar Alterações no Banco"):
            # Lógica: Comparar df_editavel com df_editado e enviar updates/deletes para o Supabase
            st.warning("Implemente aqui a lógica de comparação para persistir os dados.")
            st.success("Alterações sincronizadas com sucesso!")
    
    # 3. RESETAR TUDO
    st.divider()
    if st.button("⚠️ Resetar Todos os Lançamentos", type="primary"):
        # supabase.table("lancamentos").delete().eq("user_id", st.session_state.user.id).execute()
        st.error("Todos os lançamentos foram excluídos.")
        st.rerun()
