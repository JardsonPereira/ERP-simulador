import streamlit as st
import pandas as pd
import sys
import os

# Correção vital para importar o utils da pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

st.set_page_config(layout="wide")
inject_css("style.css")

# Autenticação Segura
user_id = check_auth()

st.title("📊 Diário de Lançamentos")

dados = get_data_cached("lancamentos", user_id)

if dados:
    df = pd.DataFrame(dados)
    
    # --- LIMPEZA DE DADOS (Resolve o StreamlitAPIException) ---
    # Convertemos tipos complexos para tipos que o Streamlit entende
    if 'valor' in df.columns:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)
    
    # Criamos um DataFrame específico para edição (sem colunas problemáticas)
    df_editavel = df[['operacao', 'valor', 'status_financeiro', 'justificativa']].copy()

    edited_df = st.data_editor(
        df_editavel, 
        use_container_width=True,
        num_rows="dynamic"
    )

    if st.button("💾 Salvar"):
        supabase = get_supabase()
        # Atualiza apenas as linhas modificadas
        for index, row in edited_df.iterrows():
            orig_id = df.loc[index, 'id'] # Recupera o ID original
            supabase.table("lancamentos").update({
                "valor": float(row["valor"]),
                "operacao": row["operacao"],
                "status_financeiro": row["status_financeiro"],
                "justificativa": row["justificativa"]
            }).eq("id", orig_id).execute()
        st.success("Salvo!")
        st.rerun()
else:
    st.info("Sem dados.")
