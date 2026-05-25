import sys
import os
import streamlit as st

# ISSO RESOLVE O IMPORT ERROR (Caminho absoluto)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, check_auth

st.title("💰 Gestão Financeira")

# ISSO RESOLVE O NAME ERROR (Definir antes de usar)
user_id = check_auth()
supabase = get_supabase()

# Teste de debug seguro
st.write(f"DEBUG: user_id autenticado: {user_id}")

# Formulário de criação de conta
nova_conta = st.text_input("Nome da nova conta:")
if st.button("Criar Conta"):
    try:
        # Tenta inserir
        supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
        st.success("Conta criada!")
        st.rerun()
    except Exception as e:
        st.error(f"Erro ao inserir no banco: {e}")
