import streamlit as st
from logic import registrar_lancamento, processar_venda_integrada

def mostrar_lancamento_manual(supabase, user_id):
    st.header("✍️ Lançamento Contábil Manual")
    with st.form("manual"):
        desc = st.text_input("Descrição")
        nat = st.selectbox("Natureza", ["Ativo Circulante", "Passivo Circulante", "Receita", "Despesa"])
        tipo = st.radio("Tipo", ["Débito", "Crédito"])
        valor = st.number_input("Valor", min_value=0.0)
        status = st.selectbox("Status", ["Pago", "Entrada", "Pendente"])
        if st.form_submit_button("Confirmar"):
            registrar_lancamento(supabase, user_id, desc, nat, tipo, valor, "Manual", status)
            st.success("Lançamento realizado!")

def mostrar_vendas_erp(supabase, user_id):
    st.header("🛒 Saída via Venda (Integrado)")
    produtos = supabase.table("produtos").select("*").execute().data
    p_nome = st.selectbox("Produto", [p['nome'] for p in produtos])
    qtd = st.number_input("Quantidade", min_value=1)
    if st.button("Confirmar Saída (Venda)"):
        prod = next(p for p in produtos if p['nome'] == p_nome)
        processar_venda_integrada(supabase, user_id, prod['id'], qtd, prod['preco_venda'])
        st.success("Saída registrada e contabilidade integrada!")
