import sys
import os
import streamlit as st
import pandas as pd

# Caminho absoluto para importar utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth, show_auth_sidebar

st.set_page_config(layout="wide")
inject_css("style.css")

# Autenticação
user = check_auth()
user_id = user.id if hasattr(user, 'id') else user.get('id')
supabase = get_supabase()
show_auth_sidebar(supabase)

LISTA_GRUPOS = ["Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido", "Despesas", "Encargos Financeiros", "Receita"]
LISTA_STATUS = ["PAGO", "PENDENTE", "ENTRADA", "INVESTIMENTO", "TRANSAÇÃO INTERNA"]

# Carregamento seguro
contas_data, lancamentos_data = [], []
try:
    contas_data = supabase.table("contas").select("*").eq("user_id", user_id).execute().data or []
    lancamentos_data = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute().data or []
except Exception as e:
    st.error(f"Erro ao carregar: {e}")

st.title("💰 Gestão Financeira")
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

with aba1:
    st.subheader("Nova Conta")
    nc = st.text_input("Nome da conta")
    if st.button("Criar Conta"):
        supabase.table("contas").insert({"nome": nc, "user_id": user_id}).execute()
        st.rerun()
    
    st.divider()
    lista_contas = {c.get("nome"): c.get("id") for c in contas_data}
    with st.form("lanc_form"):
        conta_sel = st.selectbox("Conta", list(lista_contas.keys()) if lista_contas else ["Crie uma conta"])
        grupo = st.selectbox("Grupo", LISTA_GRUPOS)
        valor = st.number_input("Valor", min_value=0.0)
        data = st.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", LISTA_STATUS)
        if st.form_submit_button("Salvar"):
            supabase.table("lancamentos").insert({"user_id": user_id, "conta_id": lista_contas.get(conta_sel), "grupo": grupo, "valor": valor, "data_lancamento": str(data), "operacao": op, "status_financeiro": status}).execute()
            st.rerun()

with aba2:
    if lancamentos_data:
        df = pd.DataFrame(lancamentos_data)
        df['Excluir'] = False
        ed = st.data_editor(df.set_index('id')[['Excluir', 'grupo', 'valor', 'operacao', 'status_financeiro']], column_config={"Excluir": st.column_config.CheckboxColumn("Excluir")}, use_container_width=True)
        if st.button("Salvar Alterações"):
            for id_l, row in ed.iterrows():
                if row['Excluir']: supabase.table("lancamentos").delete().eq("id", id_l).execute()
                else: supabase.table("lancamentos").update({"grupo": row["grupo"], "valor": float(row["valor"]), "operacao": row["operacao"], "status_financeiro": row["status_financeiro"]}).eq("id", id_l).execute()
            st.rerun()
