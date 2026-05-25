import streamlit as st
import pandas as pd
import sys
import os

# 1. Ajuste do caminho para importar o utils.py da pasta raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

# 2. Configurações Iniciais da Página
st.set_page_config(page_title="Diário de Lançamentos", layout="wide")
inject_css("style.css")

# 3. VERIFICAÇÃO DE AUTENTICAÇÃO (Deve vir antes de qualquer acesso a st.session_state)
check_auth()

# Agora que passámos pelo check_auth, é seguro aceder ao user_id
user_id = st.session_state["user"]["id"]

st.title("📊 Diário de Lançamentos")
st.markdown("Edite os valores na tabela abaixo e clique em **Salvar Edições**.")

# 4. Obtenção de dados
dados = get_data_cached("lancamentos", user_id)

# Variável para armazenar o editor
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

    # Renderiza o editor
    edited_df = st.data_editor(
        df, 
        column_config=col_config, 
        use_container_width=True,
        num_rows="dynamic"
    )
else:
    st.info("Nenhum lançamento encontrado.")

# 5. Lógica de Salvamento
if st.button("💾 Salvar Edições"):
    if edited_df is not None:
        with st.spinner("A guardar alterações..."):
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
            st.rerun() # Recarrega a página para atualizar os dados
    else:
        st.warning("Não existem dados para salvar.")
