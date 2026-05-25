import streamlit as st
import pandas as pd
import sys
import os

# Caminho absoluto para a raiz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

st.set_page_config(layout="wide")
inject_css("style.css")

# Autenticação
user_id = check_auth()
supabase = get_supabase()

# Lista de Grupos
LISTA_GRUPOS = [
    "Ativo Circulante", "Ativo Não Circulante", 
    "Passivo Circulante", "Passivo Não Circulante", 
    "Patrimônio Líquido", "Despesas", 
    "Encargos Financeiros", "Receita"
]

st.title("💰 Gestão Financeira")

# --- BUSCA DE DADOS ---
contas_data = []
lancamentos_data = []

try:
    contas_res = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    lanc_res = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    
    contas_data = contas_res.data if contas_res.data else []
    lancamentos_data = lanc_res.data if lanc_res.data else []
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

# --- ABAS ---
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

with aba1:
    lista_contas = {c.get("nome", "Sem Nome"): c.get("id") for c in contas_data}
    
    col_a, col_b = st.columns([2, 1])
    with col_a:
        nome_conta = st.selectbox("Conta", list(lista_contas.keys()) if lista_contas else ["Crie uma conta"])
    with col_b:
        nova_conta = st.text_input("Nova conta:")
        if st.button("Adicionar Conta"):
            if nova_conta:
                supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
                st.rerun()

    with st.form("form_lanc"):
        # Novo campo de Grupo
        grupo = st.selectbox("Grupo Contábil", LISTA_GRUPOS)
        
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", ["PAGO", "PENDENTE"])
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar"):
            supabase.table("lancamentos").insert({
                "user_id": user_id,
                "conta_id": lista_contas.get(nome_conta),
                "grupo": grupo, # Gravando o grupo
                "valor": valor,
                "data_lancamento": str(data),
                "operacao": op,
                "status_financeiro": status,
                "justificativa": just
            }).execute()
            st.success("Lançamento salvo com sucesso!")
            st.rerun()

with aba2:
    if lancamentos_data:
        df = pd.DataFrame(lancamentos_data)
        
        # Garantir que a coluna 'grupo' exista no DataFrame, mesmo se vazia
        if 'grupo' not in df.columns:
            df['grupo'] = None
            
        cols = ['id', 'grupo', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']
        df_editavel = df[[c for c in cols if c in df.columns]].copy()
        
        edited_df = st.data_editor(
            df_editavel.set_index('id'),
            column_config={
                "grupo": st.column_config.SelectboxColumn("Grupo", options=LISTA_GRUPOS),
                "status_financeiro": st.column_config.SelectboxColumn("Status", options=["PAGO", "PENDENTE"]),
                "operacao": st.column_config.SelectboxColumn("Operação", options=["CREDITO", "DEBITO"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
            },
            use_container_width=True
        )

        if st.button("💾 Salvar Alterações"):
            for id_lanc, row in edited_df.iterrows():
                supabase.table("lancamentos").update({
                    "grupo": row["grupo"], # Atualizando o grupo
                    "valor": float(row["valor"]),
                    "operacao": row["operacao"],
                    "status_financeiro": row["status_financeiro"],
                    "justificativa": row["justificativa"]
                }).eq("id", id_lanc).execute()
            st.success("Alterações salvas!")
            st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")
