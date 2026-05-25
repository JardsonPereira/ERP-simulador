import sys
import os
import streamlit as st
import pandas as pd

# Caminho para garantir que o utils seja encontrado
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, show_auth_sidebar, check_auth

st.set_page_config(layout="wide")

# Inicialização
user = check_auth()
user_id = user.id if hasattr(user, 'id') else user.get('id')
supabase = get_supabase()

# Exibir Menu Lateral (Logout/Usuário)
show_auth_sidebar(supabase)

st.title("💰 Gestão Financeira")

# Buscar dados (Sem filtros complexos, agora que o RLS está desligado)
try:
    contas_data = supabase.table("contas").select("*").execute().data or []
    lancamentos_data = supabase.table("lancamentos").select("*").execute().data or []
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

with aba1:
    # Criar Conta
    nova_conta = st.text_input("Nome da nova conta:")
    if st.button("➕ Criar Conta"):
        if nova_conta:
            supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
            st.rerun()
    
    # Novo Lançamento
    lista_contas = {c.get("nome"): c.get("id") for c in contas_data}
    with st.form("lanc_form"):
        conta_sel = st.selectbox("Conta", list(lista_contas.keys()) if lista_contas else ["Crie uma conta"])
        valor = st.number_input("Valor", min_value=0.0)
        grupo = st.selectbox("Grupo", ["Despesas", "Receita", "Investimento"])
        status = st.selectbox("Status", ["PAGO", "PENDENTE"])
        
        if st.form_submit_button("Salvar"):
            supabase.table("lancamentos").insert({
                "user_id": user_id, 
                "conta_id": lista_contas.get(conta_sel), 
                "valor": valor, 
                "grupo": grupo, 
                "status_financeiro": status
            }).execute()
            st.success("Salvo!")
            st.rerun()

with aba2:
    if lancamentos_data:
        df = pd.DataFrame(lancamentos_data)
        st.dataframe(df, use_container_width=True)
