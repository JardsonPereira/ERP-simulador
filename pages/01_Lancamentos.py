import streamlit as st
import pandas as pd
import sys
import os

# Adiciona o caminho raiz para importar o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

st.set_page_config(page_title="Lançamentos", layout="wide")
inject_css("style.css")

# Autenticação Segura
user_id = check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira")

aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

# --- ABA 1: NOVO LANÇAMENTO ---
with aba1:
    st.subheader("Registrar novo movimento")
    
    # Busca contas
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    contas_data = res_contas.data if res_contas.data else []
    lista_contas = {c.get("nome", "Sem Nome"): c.get("id") for c in contas_data}
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        nome_conta = st.selectbox("Conta", list(lista_contas.keys()) if lista_contas else ["Nenhuma conta criada"])
    with col_b:
        nova_conta = st.text_input("Nova conta:")
        if st.button("Adicionar Conta"):
            if nova_conta:
                supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
                st.rerun()

    with st.form("form_lancamento"):
        c1, c2 = st.columns(2)
        valor = c1.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = c2.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", ["PAGO", "PENDENTE"])
        grupo = st.text_input("Grupo (Categoria)") # Restaurado
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            supabase.table("lancamentos").insert({
                "user_id": user_id,
                "conta_id": lista_contas.get(nome_conta),
                "valor": valor,
                "data_lancamento": str(data),
                "operacao": op,
                "status_financeiro": status,
                "grupo": grupo, # Restaurado
                "justificativa": just
            }).execute()
            st.success("Lançamento salvo!")

# --- ABA 2: GERENCIAR LANÇAMENTOS ---
with aba2:
    # Busca dados
    try:
        dados = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute().data
    except:
        dados = []

    if dados:
        df = pd.DataFrame(dados)
        
        # IMPORTANTE: Se o Supabase retornar colunas com nomes diferentes, ajuste aqui
        # Exemplo: se no banco for 'status' e não 'status_financeiro', mude abaixo
        cols_exibidas = ['id', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'grupo', 'justificativa']
        
        # Filtra apenas colunas existentes para não dar erro
        df_editavel = df[[c for c in cols_exibidas if c in df.columns]].copy()
        
        st.write("Edite abaixo:")
        edited_df = st.data_editor(
            df_editavel.set_index('id'),
            column_config={
                "operacao": st.column_config.SelectboxColumn("Operação", options=["CREDITO", "DEBITO"]),
                "status_financeiro": st.column_config.SelectboxColumn("Status", options=["PAGO", "PENDENTE"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                "grupo": st.column_config.TextColumn("Grupo")
            },
            use_container_width=True
        )

        if st.button("💾 Salvar Alterações"):
            with st.spinner("Atualizando banco de dados..."):
                for id_lanc, row in edited_df.iterrows():
                    supabase.table("lancamentos").update({
                        "valor": float(row["valor"]),
                        "operacao": row["operacao"],
                        "status_financeiro": row["status_financeiro"],
                        "grupo": row.get("grupo", ""), # Restaurado
                        "justificativa": row["justificativa"]
                    }).eq("id", id_lanc).execute()
                st.success("Alterações salvas!")
                st.rerun()
    else:
        st.info("Nenhum lançamento encontrado. Crie um na aba ao lado.")
