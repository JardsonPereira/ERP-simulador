import streamlit as st
import pandas as pd
from logic import processar_venda_integrada

def mostrar_vendas_erp(supabase):
    st.header("🛒 Módulo de Vendas (Simulação ERP)")
    produtos = supabase.table("produtos").select("*").execute().data
    
    with st.form("form_venda"):
        p_nome = st.selectbox("Produto", [p['nome'] for p in produtos])
        qtd = st.number_input("Quantidade", min_value=1)
        
        if st.form_submit_button("Efetivar Venda"):
            prod = next(p for p in produtos if p['nome'] == p_nome)
            # Chama o motor lógico que faz o lançamento contábil + baixa de estoque
            processar_venda_integrada(supabase, prod['id'], qtd, prod['preco_venda'])
            st.success("Nota, Estoque e Contabilidade integrados!")

def mostrar_gestao(supabase, id_usuario):
    # Aqui você mantém seu código original de gestão e reset
    # ...
