import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o diretório pai ao caminho do sistema para importar o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

# Configuração da Página
st.set_page_config(page_title="Diário de Lançamentos", layout="wide")
inject_css("style.css")
check_auth()

st.title("📊 Diário de Lançamentos")
st.markdown("Edite os valores na tabela e clique em 'Salvar Edições'.")

# Obter dados
user_id = st.session_state["user"]["id"]
dados = get_data_cached("lancamentos", user_id)

# Variável inicializada como None para evitar erros
edited_df = None

if dados:
    df = pd.DataFrame(dados)
    
    # Configuração visual das colunas
    col_config = {
        "id": None, # Oculta IDs técnicos
        "user_id": None, 
        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
        "data_lancamento": st.column_config.DateColumn("Data"),
    }

    # O st.data_editor é chamado AQUI, fora do botão, para a variável existir sempre
    edited_df = st.data_editor(
        df, 
        column_config=col_config, 
        use_container_width=True,
        num_rows="dynamic"
    )
else:
    st.info("Nenhum lançamento encontrado.")

# Botão de Ação - Agora usa a variável edited_df que já foi definida acima
if st.button("💾 Salvar Edições"):
    if edited_df is not None:
        with st.spinner("Salvando alterações..."):
            supabase = get_supabase()
            
            # Percorre o dataframe editado e atualiza no Supabase
            for index, row in edited_df.iterrows():
                supabase.table("lancamentos").update({
                    "valor": row["valor"],
                    "operacao": row["operacao"],
                    "status_financeiro": row["status_financeiro"],
                    "justificativa": row["justificativa"]
                }).eq("id", row["id"]).execute()
                
            st.success("Alterações salvas com sucesso!")
            st.rerun() # Recarrega a página para refletir as mudanças
    else:
        st.warning("Não existem dados para salvar.")
