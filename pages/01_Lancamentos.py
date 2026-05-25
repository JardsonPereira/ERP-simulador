import streamlit as st
import pandas as pd
import sys
import os

# Ajuste de caminho para garantir que importa o utils.py da raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

# Configuração da Página
st.set_page_config(page_title="Lançamentos", layout="wide")
inject_css("style.css")

# Autenticação Segura
user_id = check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira")

# Abas para organizar a interface
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

# --- ABA 1: NOVO LANÇAMENTO ---
with aba1:
    st.subheader("Registrar novo movimento")
    
    # Buscar contas existentes de forma segura
    try:
        res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
        contas_data = res_contas.data if res_contas.data else []
    except:
        contas_data = []
    
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
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data")
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
    # Buscar Lançamentos
    try:
        dados = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute().data
    except:
        dados = []

    if dados:
        df = pd.DataFrame(dados)
        
        # LIMPEZA OBRIGATÓRIA PARA O EDITOR (Resolve StreamlitAPIException)
        df_editavel = df[['id', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']].copy()
        
        # Configuração do editor
        edited_df = st.data_editor(
            df_editavel.set_index('id'), 
            use_container_width=True
        )

        if st.button("💾 Salvar Alterações"):
            with st.spinner("Atualizando banco de dados..."):
                for id_lanc, row in edited_df.iterrows():
                    supabase.table("lancamentos").update({
                        "valor": float(row["valor"]),
                        "operacao": row["operacao"],
                        "status_financeiro": row["status_financeiro"],
                        "justificativa": row["justificativa"]
                    }).eq("id", id_lanc).execute()
                st.success("Alterações salvas!")
                st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")
