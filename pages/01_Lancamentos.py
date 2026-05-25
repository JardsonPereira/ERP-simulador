import streamlit as st
import pandas as pd
import sys
import os

# Ajuste para importar o utils corretamente (caso esteja na raiz)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

st.set_page_config(page_title="Diário de Lançamentos", layout="wide")
inject_css("style.css")
check_auth()

st.title("📊 Diário de Lançamentos")
st.markdown("Edite os valores diretamente na tabela abaixo e clique em Salvar.")

user_id = st.session_state["user"]["id"]
dados = get_data_cached("lancamentos", user_id)

if dados:
    df = pd.DataFrame(dados)
    
    # Configuração visual das colunas
    col_config = {
        "id": None, # Oculta o ID técnico
        "user_id": None, 
        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
        "data_lancamento": st.column_config.DateColumn("Data"),
    }

    # Tabela editável
    edited_df = st.data_editor(
        df, 
        column_config=col_config, 
        use_container_width=True,
        num_rows="dynamic"
    )

    # Botões de Ação
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("💾 Salvar Edições"):
            with st.spinner("Salvando..."):
                supabase = get_supabase()
                # Atualiza cada linha modificada no Supabase
                for index, row in edited_df.iterrows():
                    supabase.table("lancamentos").update({
                        "valor": row["valor"],
                        "operacao": row["operacao"],
                        "status_financeiro": row["status_financeiro"],
                        "justificativa": row["justificativa"]
                    }).eq("id", row["id"]).execute()
                st.success("Alterações salvas!")
                st.rerun()
else:
    st.info("Nenhum lançamento encontrado.")
