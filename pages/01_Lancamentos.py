import streamlit as st
from supabase import create_client

# Configurações (certifique-se que o st.secrets está configurado)
url = st.secrets["https://ejdvfuczdnpyhuosruey.supabase.co"]
key = st.secrets["sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"]
supabase = create_client(url, key)

st.title("Lançamentos Financeiros")

# --- RECUPERAÇÃO SEGURA DA SESSÃO ---
# Em vez de get_user(), usamos a sessão, que persiste durante a navegação
session = supabase.auth.get_session()

if not session:
    st.error("Sessão não encontrada. Por favor, faça login novamente no menu principal.")
    st.stop()

# Agora temos o ID com segurança
user_id = session.user.id
st.write(f"Usuário logado ID: {user_id}")
