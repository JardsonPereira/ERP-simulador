import streamlit as st
from supabase import create_client

# Inicialização (ajuste conforme seu arquivo app.py)
supabase = create_client(st.secrets["https://ejdvfuczdnpyhuosruey.supabase.co"], st.secrets["sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"])

st.title("Lançamentos Financeiros")

# --- A FORMA CORRETA DE PEGAR O USUÁRIO ---
try:
    # Tenta pegar a sessão atual
    session = supabase.auth.get_session()
    if not session:
        st.error("Sessão expirada. Por favor, faça login novamente.")
        st.stop()
    
    user_id = session.user.id
except Exception as e:
    st.error("Erro ao autenticar usuário.")
    st.stop()
