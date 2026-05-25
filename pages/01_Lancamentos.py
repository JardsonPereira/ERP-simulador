import streamlit as st
from supabase import create_client
from datetime import date

# CONFIGURAÇÃO DIRETA (Use suas chaves)
URL = "https://ejdvfuczdnpyhuosruey.supabase.co"
KEY = "sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"

# Inicializa o cliente do Supabase
supabase = create_client(URL, KEY)

st.title("Lançamentos Financeiros")

# --- SEGURANÇA E SESSÃO ---
# Mantemos sua lógica de verificar sessão antes de exibir qualquer coisa
session = supabase.auth.get_session()

if not session:
    st.error("Sessão expirada. Por favor, faça login na página principal.")
    st.stop()

user_id = session.user.id

# --- FORMULÁRIO DE LANÇAMENTO (Sua lógica mantida) ---
with st.form("lancamento_form"):
    col1, col2 = st.columns(2)
    with col1:
        data = st.date_input("Data", date.today())
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    with col2:
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        descricao = st.text_input("Descrição")
    
    submit = st.form_submit_button("Salvar Lançamento")

    if submit:
        dados = {
            "user_id": user_id,
            "data": str(data),
            "descricao": descricao,
            "valor": valor,
            "tipo": tipo
        }
        try:
            # Envia para a tabela 'lancamentos'
            supabase.table("lancamentos").insert(dados).execute()
            st.success("Lançamento salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- LISTAGEM ---
st.subheader("Seus Últimos Lançamentos")
try:
    response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data", desc=True).execute()
    if response.data:
        st.table(response.data)
    else:
        st.info("Nenhum lançamento encontrado.")
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
