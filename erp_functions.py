import streamlit as st
import pandas as pd
from logic import processar_venda_integrada

def mostrar_vendas_erp(supabase, user_id):
    st.header("🛒 Saída via Venda (Integrado)")
    resp = supabase.table("produtos").select("*").execute()
    produtos = resp.data if resp.data else []
    
    if not produtos:
        st.warning("Cadastre produtos no menu Gestão.")
        return

    p_nome = st.selectbox("Produto", [p['nome'] for p in produtos])
    qtd = st.number_input("Quantidade", min_value=1)
    if st.button("Confirmar Saída (Venda)"):
        prod = next(p for p in produtos if p['nome'] == p_nome)
        processar_venda_integrada(supabase, user_id, prod['id'], qtd, prod['preco_venda'])
        st.success("Operação concluída!")

def mostrar_gestao(supabase, user_id):
    st.header("⚙️ Gestão de Cadastros")
    resp = supabase.table("produtos").select("*").execute()
    if resp.data:
        df = pd.DataFrame(resp.data)
        st.table(df) # Exibe a tabela completa
    
    with st.form("add_prod"):
        nome = st.text_input("Nome do Produto")
        cat = st.selectbox("Categoria", ["Produtos", "Serviços"])
        preco = st.number_input("Preço de Venda")
        if st.form_submit_button("Cadastrar"):
            supabase.table("produtos").insert({
                "nome": nome, "categoria": cat, "preco_venda": preco, "saldo_estoque": 100
            }).execute()
            st.rerun()
