import streamlit as st
from logic import registrar_lancamento

def mostrar_lancamentos(supabase, user_id):
    col1, col2 = st.columns(2)
    
    # ENTRADAS
    with col1:
        st.subheader("📥 Entrada (Recebimentos/Investimentos)")
        with st.form("entrada"):
            desc = st.text_input("Descrição")
            nat = st.selectbox("Grupo", ["Ativo Circulante", "Patrimônio Líquido", "Receitas", "Investimentos"])
            tipo = st.radio("Operação", ["Débito", "Crédito"])
            valor = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Entrada", "Pendente", "Investimento", "Transação Interna"])
            data = st.date_input("Data")
            just = st.text_area("Justificativa")
            if st.form_submit_button("Confirmar Entrada"):
                registrar_lancamento(supabase, user_id, desc, nat, tipo, valor, just, status, data)
                st.success("Entrada registrada!")

    # SAÍDAS
    with col2:
        st.subheader("📤 Saída (Pagamentos/Despesas)")
        with st.form("saida"):
            desc = st.text_input("Descrição")
            nat = st.selectbox("Grupo", ["Passivo Circulante", "CMV", "Despesas", "Encargos Financeiros"])
            tipo = st.radio("Operação", ["Débito", "Crédito"])
            valor = st.number_input("Valor", min_value=0.0)
            status = st.selectbox("Status", ["Pago", "Pendente"])
            data = st.date_input("Data")
            just = st.text_area("Justificativa")
            if st.form_submit_button("Confirmar Saída"):
                registrar_lancamento(supabase, user_id, desc, nat, tipo, valor, just, status, data)
                st.success("Saída registrada!")
