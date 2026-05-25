import streamlit as st
from supabase import create_client

# Configurações
url = st.secrets["https://ejdvfuczdnpyhuosruey.supabase.co"]
key = st.secrets["sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"]
supabase = create_client(url, key)

st.title("Lançamentos Financeiros")

# --- RECUPERAÇÃO ROBUSTA DA SESSÃO ---
session = supabase.auth.get_session()

if not session:
    st.error("Sessão expirada. Por favor, retorne à página inicial e faça login novamente.")
    st.stop()

# Acessar o usuário de forma segura
user = session.user
if user is None:
    st.error("Não foi possível identificar o usuário logado.")
    st.stop()

user_id = user.id  # Agora garantimos que o user não é None
st.write(f"Usuário autenticado: {user.email}")
