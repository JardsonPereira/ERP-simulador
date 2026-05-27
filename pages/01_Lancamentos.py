
import streamlit as st
from utils import get_supabase_client, check_auth

# Verifica a sessão antes de qualquer coisa
session = check_auth()
supabase = get_supabase_client()

user_id = session.user.id

# ... resto do seu código de lançamentos ...import streamlit as st
from supabase import create_client
from datetime import date

# 1. SEGURANÇA: Use o arquivo .streamlit/secrets.toml
# No arquivo secrets.toml, coloque:
# SUPABASE_URL = "sua_url"
# SUPABASE_KEY = "sua_key"
supabase = create_client(URL, KEY)

st.title("💰 Lançamentos Financeiros")

# --- SEGURANÇA E SESSÃO ---
session = supabase.auth.get_session()

if not session:
    st.error("Sessão expirada. Por favor, faça login.")
    st.stop()

user_id = session.user.id

# --- FORMULÁRIO ---
with st.form("lancamento_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", date.today())
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    with col2:
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        descricao = st.text_input("Descrição")
    
    submit = st.form_submit_button("Salvar Lançamento")

    if submit:
        if not descricao:
            st.warning("A descrição é obrigatória!")
        else:
            dados = {
                "user_id": user_id,
                "data": str(data),
                "descricao": descricao,
                "valor": valor if tipo == "Receita" else -valor, # Lógica de sinal
                "tipo": tipo
            }
            try:
                supabase.table("lancamentos").insert(dados).execute()
                st.success("Lançamento salvo!")
                st.rerun() # Atualiza a página para mostrar o novo dado
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# --- LISTAGEM ---
st.subheader("Histórico")
response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data", desc=True).execute()

if response.data:
    st.dataframe(response.data, use_container_width=True)
else:
    st.info("Nenhum lançamento encontrado.")
