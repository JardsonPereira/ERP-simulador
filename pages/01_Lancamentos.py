import streamlit as st
import pandas as pd
import sys
import os

# 1. Configuração e Autenticação
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

st.set_page_config(page_title="Gestão Financeira", layout="wide")
inject_css("style.css")

user_id = check_auth()
supabase = get_supabase()

# 2. BUSCA GLOBAL DE DADOS (Executada uma única vez no início)
def carregar_dados():
    try:
        res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
        res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
        return pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame(), res_contas.data
    except Exception as e:
        st.error(f"Erro ao conectar com banco: {e}")
        return pd.DataFrame(), []

df_lancamentos, contas_data = carregar_dados()

st.title("💰 Gestão Financeira")

# 3. CRIAÇÃO DAS ABAS
aba0, aba1, aba2 = st.tabs(["📊 Resumo", "➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

# --- ABA 0: RESUMO (Reflete os dados puxados) ---
with aba0:
    st.subheader("Resumo Geral")
    if not df_lancamentos.empty:
        # Exemplo: Calcula total de créditos e débitos
        total_cred = df_lancamentos[df_lancamentos['operacao'] == 'CREDITO']['valor'].sum()
        total_deb = df_lancamentos[df_lancamentos['operacao'] == 'DEBITO']['valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Entradas", f"R$ {total_cred:.2f}")
        c2.metric("Total Saídas", f"R$ {total_deb:.2f}")
        c3.metric("Saldo", f"R$ {total_cred - total_deb:.2f}")
        
        st.dataframe(df_lancamentos, use_container_width=True)
    else:
        st.info("Nenhum dado para resumir.")

# --- ABA 1: NOVO LANÇAMENTO ---
with aba1:
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
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar"):
            supabase.table("lancamentos").insert({
                "user_id": user_id,
                "conta_id": lista_contas.get(nome_conta),
                "valor": valor,
                "data_lancamento": str(data),
                "operacao": op,
                "status_financeiro": status,
                "justificativa": just
            }).execute()
            st.success("Salvo!")
            st.rerun() # Recarrega para refletir na Aba 0 e 2

# --- ABA 2: GERENCIAR LANÇAMENTOS ---
with aba2:
    if not df_lancamentos.empty:
        # Prepara colunas para edição
        colunas = ['id', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']
        df_editavel = df_lancamentos[colunas].copy()
        
        edited_df = st.data_editor(
            df_editavel.set_index('id'),
            column_config={
                "status_financeiro": st.column_config.SelectboxColumn("Status", options=["PAGO", "PENDENTE"]),
                "operacao": st.column_config.SelectboxColumn("Operação", options=["CREDITO", "DEBITO"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
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
            st.success("Alterações salvas!")
            st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")
