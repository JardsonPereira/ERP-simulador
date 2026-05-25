import streamlit as st
from supabase import create_client
from datetime import date

# Configuração Supabase (deve ser a mesma do app.py)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("Lançamentos Financeiros")

# 1. SEGURANÇA: Verificar se o usuário está logado
if 'user' not in st.session_state or not st.session_state.user:
    st.error("Acesso não autorizado. Por favor, faça login.")
    st.stop()

user_id = supabase.auth.get_user().user.id

# 2. FORMULÁRIO DE LANÇAMENTO
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
        # Envio para o Supabase
        dados = {
            "user_id": user_id,
            "data": str(data),
            "descricao": descricao,
            "valor": valor,
            "tipo": tipo
        }
        try:
            supabase.table("lancamentos").insert(dados).execute()
            st.success("Lançamento salvo com sucesso!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# 3. LISTAGEM DOS LANÇAMENTOS
st.subheader("Últimos Lançamentos")
try:
    response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data", desc=True).execute()
    if response.data:
        st.table(response.data)
    else:
        st.info("Nenhum lançamento encontrado.")
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
