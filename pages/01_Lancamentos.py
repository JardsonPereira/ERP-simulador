import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, resetar_lancamentos, deletar_lancamento_por_id

st.set_page_config(layout="wide")
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("⚖️ Gestão Contábil Profissional")

# --- Aba de Cadastro ---
with st.expander("➕ Novo Lançamento Contábil"):
    with st.form("form_novo", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data do Fato")
            conta = st.text_input("Nome da Conta")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        with col2:
            grupo = st.selectbox("Grupo", ["Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido", "Receita", "Despesa", "Encargos Financeiros"])
            operacao = st.radio("Natureza", ["Débito", "Crédito"])
            status = st.selectbox("Status", ["Entrada", "Pago", "Pendente", "Investimento", "Transação Interna"])
        
        justificativa = st.text_area("Justificativa / Histórico")
        
        if st.form_submit_button("Registrar Lançamento"):
            supabase.table("lancamentos").insert({
                "user_id": user_id, "data": str(data), "conta": conta, 
                "grupo": grupo, "operacao": operacao, "valor": valor, 
                "status": status, "justificativa": justificativa
            }).execute()
            st.success("Lançamento efetuado com sucesso!")
            st.rerun()

# --- Gestão e Edição ---
st.subheader("Diário de Lançamentos")
df = pd.DataFrame(get_data_cached("lancamentos", user_id))

if not df.empty:
    # Edição Interativa
    st.info("Dica: Edite os valores diretamente na tabela abaixo.")
    df_editado = st.data_editor(df, use_container_width=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💾 Salvar Edições"):
            # Lógica simples: detectar alterações linha a linha (requer backend adicional)
            st.warning("Funcionalidade de salvamento em lote em implementação.")
    with col_b:
        if st.button("🔥 Resetar Todos os Dados", type="primary"):
            if st.checkbox("Confirmar reset total?"):
                resetar_lancamentos(user_id)
                st.rerun()
else:
    st.write("Nenhum lançamento encontrado.")
