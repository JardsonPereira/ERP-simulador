import streamlit as st
import pandas as pd

def mostrar_gestao(supabase, user_id):
    st.header("⚙️ Gestão de Cadastros")
    resp = supabase.table("produtos").select("*").execute()
    data = resp.data if resp.data else []
    
    if data:
        df = pd.DataFrame(data)
        # Exibição segura
        cols = ['nome', 'categoria', 'preco_venda', 'saldo_estoque']
        # Verifica se as colunas existem antes de exibir
        colunas_disponiveis = [c for c in cols if c in df.columns]
        st.table(df[colunas_disponiveis])
    else:
        st.info("Nenhum produto cadastrado.")
