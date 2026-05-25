import streamlit as st
import pandas as pd
import sys
import os

# Ajuste de caminho obrigatório em TODAS as páginas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

st.set_page_config(page_title="Gestão Financeira", layout="wide")
inject_css("style.css")

# Autenticação centralizada
user_id = check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira")

# --- FUNÇÃO CENTRAL DE DADOS ---
def carregar_dados_banco():
    # Busca lançamentos e contas
    lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute().data
    contas = supabase.table("contas").select("*").eq("user_id", user_id).execute().data
    return pd.DataFrame(lanc) if lanc else pd.DataFrame(), contas

# Carrega os dados uma vez e guarda no estado da sessão
if "df_lancamentos" not in st.session_state:
    st.session_state["df_lancamentos"], st.session_state["contas"] = carregar_dados_banco()

df = st.session_state["df_lancamentos"]
contas_data = st.session_state["contas"]

# ABAS
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

with aba1:
    st.subheader("Registrar novo movimento")
    lista_contas = {c.get("nome", "Sem Nome"): c.get("id") for c in contas_data}
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        nome_conta = st.selectbox("Conta", list(lista_contas.keys()) if lista_contas else ["Crie uma conta"])
    with col_b:
        nova_conta = st.text_input("Nova conta:")
        if st.button("Adicionar Conta"):
            supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
            st.rerun()

    with st.form("form_lanc"):
        valor = st.number_input("Valor", min_value=0.0, step=0.01)
        data = st.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", ["PAGO", "PENDENTE"])
        grupo = st.text_input("Grupo (Categoria)") 
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            # Nota: O banco precisa ter a coluna 'grupo' criada lá no Supabase!
            payload = {
                "user_id": user_id, "conta_id": lista_contas.get(nome_conta),
                "valor": valor, "data_lancamento": str(data),
                "operacao": op, "status_financeiro": status,
                "justificativa": just
            }
            # Adiciona 'grupo' apenas se ele existir no banco
            supabase.table("lancamentos").insert(payload).execute()
            st.success("Salvo!")
            del st.session_state["df_lancamentos"] # Força recarregar
            st.rerun()

with aba2:
    if not df.empty:
        # Colunas permitidas (Ajuste se o banco tiver nomes diferentes)
        cols = ['id', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']
        df_editavel = df[[c for c in cols if c in df.columns]].copy()
        
        edited_df = st.data_editor(
            df_editavel.set_index('id'),
            column_config={
                "status_financeiro": st.column_config.SelectboxColumn("Status", options=["PAGO", "PENDENTE"]),
                "operacao": st.column_config.SelectboxColumn("Operação", options=["CREDITO", "DEBITO"])
            },
            use_container_width=True
        )

        if st.button("💾 Salvar Alterações"):
            for id_lanc, row in edited_df.iterrows():
                supabase.table("lancamentos").update({
                    "valor": float(row["valor"]),
                    "operacao": row["operacao"],
                    "status_financeiro": row["status_financeiro"],
                    "justificativa": row["justificativa"]
                }).eq("id", id_lanc).execute()
            del st.session_state["df_lancamentos"] # Força recarregar
            st.success("Alterações salvas!")
            st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")
