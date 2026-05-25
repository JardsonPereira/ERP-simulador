import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o caminho para importar o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, get_supabase, inject_css, check_auth

st.set_page_config(page_title="Lançamentos", layout="wide")
inject_css("style.css")

# Autenticação Segura
user_id = check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira")

# Criamos Abas para organizar a interface
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

# --- ABA 1: NOVO LANÇAMENTO ---
with aba1:
    st.subheader("Registrar novo movimento")
    
    # Gestão de Contas (Buscar do Supabase)
    contas_data = supabase.table("contas").select("*").eq("user_id", user_id).execute().data
    lista_contas = {c["nome"]: c["id"] for c in contas_data}
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        nome_conta = st.selectbox("Conta", list(lista_contas.keys()) if lista_contas else ["Nenhuma conta criada"])
    with col_b:
        nova_conta = st.text_input("Criar nova conta:")
        if st.button("Adicionar Conta"):
            if nova_conta:
                supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
                st.rerun()

    # Formulário de Lançamento
    with st.form("form_lancamento"):
        c1, c2 = st.columns(2)
        valor = c1.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = c2.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", ["PAGO", "PENDENTE"])
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            supabase.table("lancamentos").insert({
                "user_id": user_id,
                "conta_id": lista_contas.get(nome_conta),
                "valor": valor,
                "data_lancamento": str(data),
                "operacao": op,
                "status_financeiro": status,
                "justificativa": just
            }).execute()
            st.success("Lançamento salvo!")

# --- ABA 2: GERENCIAR LANÇAMENTOS ---
with aba2:
    dados = get_data_cached("lancamentos", user_id)
    if dados:
        df = pd.DataFrame(dados)
        df_editavel = df[['id', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']].copy()
        
        # Editor Editável
        edited_df = st.data_editor(
            df_editavel.set_index('id'), # ID como índice para facilitar edição
            use_container_width=True
        )

        col_acao1, col_acao2 = st.columns(2)
        
        with col_acao1:
            if st.button("💾 Salvar Alterações"):
                for id_lanc, row in edited_df.iterrows():
                    supabase.table("lancamentos").update({
                        "valor": float(row["valor"]),
                        "operacao": row["operacao"],
                        "status_financeiro": row["status_financeiro"],
                        "justificativa": row["justificativa"]
                    }).eq("id", id_lanc).execute()
                st.success("Alterações salvas!")
                st.rerun()
        
        with col_acao2:
            if st.button("🗑️ Resetar Tudo (Apagar Lançamentos)"):
                if st.checkbox("Confirmar exclusão de TODOS os lançamentos?"):
                    supabase.table("lancamentos").delete().eq("user_id", user_id).execute()
                    st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")
