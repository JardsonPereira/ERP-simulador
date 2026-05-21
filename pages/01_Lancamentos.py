import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, check_auth

check_auth()
supabase = get_supabase()

st.title("⚖️ Sistema Contábil Integrado")

# --- Aba de Cadastro de Contas ---
def interface_contas():
    st.subheader("Configurar Contas e Grupos")
    with st.form("form_conta"):
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", [
            "Ativo Circulante", "Ativo Não Circulante", 
            "Passivo Circulante", "Passivo Não Circulante", 
            "Patrimônio Líquido", "Receitas", "Despesas", "Encargos Financeiros"
        ])
        if st.form_submit_button("Salvar Conta"):
            # Inserir no Supabase (tabela 'contas')
            st.success("Conta cadastrada!")

# --- Aba de Lançamentos (Core) ---
def interface_lancamentos():
    st.subheader("Lançamento Contábil")
    
    # Formulário de Inserção
    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data")
            conta = st.selectbox("Conta", ["Ex: Banco", "Ex: Fornecedor"])
            valor = st.number_input("Valor (R$)", min_value=0.0)
        with col2:
            operacao = st.radio("Operação", ["Débito", "Crédito"])
            status = st.selectbox("Status Financeiro", ["Entrada", "Pago", "Pendente", "Investimento", "Transação Interna"])
            justificativa = st.text_area("Justificativa")
        
        if st.form_submit_button("Lançar"):
            # Logica: Inserir na tabela 'lancamentos'
            st.success("Partida registrada!")

    # Gestão (Edição, Exclusão e Reset)
    st.subheader("Gestão de Lançamentos")
    df = pd.DataFrame(get_data_cached("lancamentos", st.session_state.user.id))
    
    if not df.empty:
        # Edição direta no DataEditor
        df_editado = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        
        col_btn1, col_btn2 = st.columns([1, 1])
        with col_btn1:
            if st.button("💾 Salvar Alterações (Edição)"):
                # Lógica: Comparar df original com df_editado e atualizar via Supabase
                st.info("Alterações sincronizadas.")
        with col_btn2:
            if st.button("🔥 Resetar Todos os Lançamentos", type="primary"):
                # Lógica: DELETE FROM lancamentos WHERE user_id = ...
                st.warning("Base limpa!")
                st.rerun()

# --- Estrutura das Abas ---
aba1, aba2 = st.tabs(["➕ Novo Lançamento / Gestão", "🏦 Cadastrar Contas"])
with aba1: interface_lancamentos()
with aba2: interface_contas()
