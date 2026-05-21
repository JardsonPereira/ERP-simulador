import streamlit as st
import pandas as pd
from logic import processar_venda_integrada

def mostrar_vendas_erp(supabase):
    st.header("🛒 Módulo de Vendas (Simulação ERP)")
    produtos = supabase.table("produtos").select("*").execute().data
    
    with st.form("form_venda"):
        p_nome = st.selectbox("Produto", [p['nome'] for p in produtos])
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        
        if st.form_submit_button("Efetivar Venda"):
            try:
                prod = next(p for p in produtos if p['nome'] == p_nome)
                processar_venda_integrada(supabase, prod['id'], qtd, prod['preco_venda'])
                st.success("Nota, Estoque e Contabilidade integrados!")
            except Exception as e:
                st.error(f"Erro na integração: {e}")

def mostrar_gestao(supabase, id_usuario):
    st.header("⚙️ Gestão de Cadastros")
    with st.expander("Cadastrar Novo Produto (WMS)"):
        with st.form("add_prod"):
            nome = st.text_input("Nome do Produto")
            cat = st.selectbox("Categoria", ["Produtos", "Serviços"])
            preco = st.number_input("Preço de Venda")
            if st.form_submit_button("Cadastrar"):
                supabase.table("produtos").insert({
                    "nome": nome, "categoria": cat, "preco_venda": preco, "saldo_estoque": 100
                }).execute()
                st.rerun()

def mostrar_razonetes(supabase, user_id, filtro):
    st.header("📊 Razonetes")
    # ... (seu código original de Razonetes aqui)

def mostrar_balancete(supabase, filtro):
    st.header("🧾 Balancete")
    # ... (seu código original de Balancete aqui)

def mostrar_dre(df_periodo):
    st.header("📈 DRE")
    # ... (seu código original de DRE aqui)

def mostrar_fluxo_caixa(df_periodo, df_balanco):
    st.header("💸 Fluxo de Caixa")
    # ... (seu código original de Fluxo aqui)
