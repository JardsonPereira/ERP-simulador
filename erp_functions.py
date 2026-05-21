import streamlit as st
import pandas as pd
from logic import processar_venda_integrada

def mostrar_vendas_erp(supabase):
    st.header("🛒 Módulo de Vendas")
    # Busca produtos e trata erro se a tabela estiver vazia
    resp = supabase.table("produtos").select("*").execute()
    produtos = resp.data if resp.data else []
    
    if not produtos:
        st.warning("Cadastre produtos no menu Gestão primeiro.")
        return

    with st.form("form_venda"):
        p_nome = st.selectbox("Produto", [p['nome'] for p in produtos])
        qtd = st.number_input("Quantidade", min_value=1, step=1)
        if st.form_submit_button("Efetivar Venda"):
            prod = next(p for p in produtos if p['nome'] == p_nome)
            processar_venda_integrada(supabase, prod['id'], qtd, prod['preco_venda'])
            st.success("Operação integrada com sucesso!")

def mostrar_gestao(supabase):
    st.header("⚙️ Gestão de Cadastros")
    # ... (seu código de gestão aqui)

def mostrar_razonetes(supabase):
    st.header("📊 Razonetes")
    # Exemplo: dados = supabase.table("lancamentos").select("*").execute().data
    st.info("Função Razonetes em desenvolvimento.")

def mostrar_balancete(supabase):
    st.header("🧾 Balancete")
    st.info("Função Balancete em desenvolvimento.")

def mostrar_dre(supabase):
    st.header("📈 DRE")
    st.info("Função DRE em desenvolvimento.")

def mostrar_fluxo_caixa(supabase):
    st.header("💸 Fluxo de Caixa")
    st.info("Função Fluxo de Caixa em desenvolvimento.")
