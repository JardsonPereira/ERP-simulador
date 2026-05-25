import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o diretório raiz ao caminho para importar o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

st.set_page_config(page_title="Lançamentos", layout="wide")
inject_css("style.css")

# Autenticação Segura
user_id = check_auth()

st.title("📊 Diário de Lançamentos")

# 1. Carregar dados
dados = get_data_cached("lancamentos", user_id)

if dados:
    df = pd.DataFrame(dados)

    # 2. LIMPEZA OBRIGATÓRIA (Isso resolve o StreamlitAPIException)
    # Garantimos que as colunas críticas sejam numéricas ou strings puras
    if 'valor' in df.columns:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Converter datas para o formato datetime correto
    if 'data_lancamento' in df.columns:
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'], errors='coerce')

    # Selecionar apenas colunas editáveis para evitar erros de tipos desconhecidos
    # Ocultamos ID e user_id do editor para não causar conflitos
    colunas_para_editar = ['operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']
    df_editavel = df[colunas_para_editar]

    # Configuração explícita das colunas
    col_config = {
        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
        "data_lancamento": st.column_config.DateColumn("Data"),
        "operacao": st.column_config.SelectboxColumn("Operação", options=["CREDITO", "DEBITO"]),
    }

    # 3. Renderiza o editor usando o DataFrame limpo
    edited_df = st.data_editor(
        df_editavel, 
        column_config=col_config, 
        use_container_width=True,
        num_rows="dynamic"
    )

    # 4. Salvar (Reconstruindo os IDs perdidos)
    if st.button("💾 Salvar Edições"):
        with st.spinner("Salvando..."):
            supabase = get_supabase()
            
            # Precisamos mesclar o edited_df com o ID original para saber o que atualizar
            # Como a ordem das linhas pode mudar no editor, usamos o índice original
            for index, row in edited_df.iterrows():
                original_id = df.loc[index, 'id'] # Recupera o ID baseado na posição
                
                supabase.table("lancamentos").update({
                    "valor": float(row["valor"]),
                    "operacao": row["operacao"],
                    "status_financeiro": row["status_financeiro"],
                    "justificativa": row["justificativa"],
                    "data_lancamento": str(row["data_lancamento"])
                }).eq("id", original_id).execute()
                
            st.success("Alterações salvas!")
            st.rerun()
else:
    st.info("Nenhum lançamento encontrado.")
