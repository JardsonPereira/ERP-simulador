import streamlit as st
import sys
import os
from datetime import date

# --- CORREÇÃO DO IMPORT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

# --- INICIALIZAÇÃO E AUTENTICAÇÃO ---
user = check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)

user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)

# --- INTERFACE PRINCIPAL ---
st.title("💰 Lançamentos Financeiros")

# --- FORMULÁRIO PARA NOVO LANÇAMENTO ---
st.subheader("Novo Lançamento")

with st.form("lancamento_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data_input = st.date_input("Data", date.today())
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        # O conta_id é necessário pelo seu banco de dados. 
        # Coloque o ID numérico da conta que você já tem cadastrada (ex: 1, 2, etc.)
        conta_id = st.number_input("ID da Conta", min_value=1, step=1) 
    with col2:
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        descricao = st.text_input("Operação / Descrição")
    
    submit = st.form_submit_button("Guardar Lançamento")

    if submit:
        if not descricao:
            st.warning("A descrição é obrigatória!")
        elif not user_id:
            st.error("Erro ao identificar o utilizador. Por favor, inicie sessão novamente.")
        else:
            # Usando os nomes EXATOS das colunas que vi na foto do seu Supabase
            dados = {
                "user_id": user_id,
                "data_lancamento": str(data_input),
                "operacao": descricao,           # Ajustado para 'operacao'
                "status_financeiro": tipo,       # Ajustado para 'status_financeiro'
                "conta_id": conta_id,            # A chave estrangeira que faltava
                "valor": valor if tipo == "Receita" else -valor
            }
            try:
                supabase.table("lancamentos").insert(dados).execute()
                st.success("Lançamento guardado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao guardar: {e}")

# --- LISTAGEM (HISTÓRICO) ---
st.markdown("---")
st.subheader("Histórico de Lançamentos")

if user_id:
    try:
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
        
        if response.data:
            st.dataframe(response.data, use_container_width=True)
        else:
            st.info("Nenhum lançamento encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
