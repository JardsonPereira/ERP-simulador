import streamlit as st
import pandas as pd
import sys
import os

# Ajuste de caminho para importar o utils da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

# 1. Configurações Iniciais
st.set_page_config(page_title="Diário de Lançamentos", layout="wide")
inject_css("style.css")

# 2. Autenticação Segura (Retorna o ID e para a execução se falhar)
user_id = check_auth()

st.title("📊 Diário de Lançamentos")

# 3. Carregamento de Dados
dados = get_data_cached("lancamentos", user_id)

# 4. Inicialização do Editor (Fora do bloco de botão para evitar erros)
edited_df = None

if dados:
    df = pd.DataFrame(dados)
    
    col_config = {
        "id": None, 
        "user_id": None, 
        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
        "data_lancamento": st.column_config.DateColumn("Data"),
    }

    # O editor sempre existe, independentemente de clicar no botão ou não
    edited_df = st.data_editor(
        df, 
        column_config=col_config, 
        use_container_width=True,
        num_rows="dynamic"
    )
else:
    st.info("Nenhum lançamento encontrado.")

# 5. Botão de Salvar
if st.button("💾 Salvar Edições"):
    if edited_df is not None:
        with st.spinner("Salvando alterações no Supabase..."):
            supabase = get_supabase()
            
            # Atualiza cada linha no banco
            for index, row in edited_df.iterrows():
                supabase.table("lancamentos").update({
                    "valor": row["valor"],
                    "operacao": row["operacao"],
                    "status_financeiro": row["status_financeiro"],
                    "justificativa": row["justificativa"]
                }).eq("id", row["id"]).execute()
                
            st.success("Alterações salvas com sucesso!")
            st.rerun() 
    else:
        st.warning("Não há dados para salvar.")
