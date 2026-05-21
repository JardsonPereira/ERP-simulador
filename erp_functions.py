import streamlit as st
import pandas as pd
from logic import processar_venda_integrada

def mostrar_gestao(supabase, user_id):
    st.header("⚙️ Gestão de Produtos")
    
    # 1. Leitura segura
    resp = supabase.table("produtos").select("*").execute()
    data = resp.data if resp.data else []
    
    if data:
        st.table(pd.DataFrame(data))
    else:
        st.info("Nenhum produto cadastrado.")
    
    # 2. Cadastro
    with st.form("add_prod"):
        nome = st.text_input("Nome")
        cat = st.selectbox("Categoria", ["Produtos", "Serviços"])
        preco = st.number_input("Preço", min_value=0.0)
        if st.form_submit_button("Cadastrar"):
            supabase.table("produtos").insert({
                "nome": nome, "categoria": cat, "preco_venda": preco, "saldo_estoque": 100
            }).execute()
            st.rerun()

def mostrar_vendas_erp(supabase, user_id):
    st.header("🛒 Saída via Venda")
    resp = supabase.table("produtos").select("*").execute()
    produtos = resp.data if resp.data else []
    
    if not produtos: return
    
    p_sel = st.selectbox("Produto", [p['nome'] for p in produtos])
    qtd = st.number_input("Qtd", min_value=1)
    
    if st.button("Confirmar Venda"):
        prod = next(p for p in produtos if p['nome'] == p_sel)
        processar_venda_integrada(supabase, user_id, prod['id'], qtd, prod['preco_venda'])
        st.success("Venda integrada!")
