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
st.title("💰 Lançamentos nos Razonetes")
st.markdown("Efetue novos lançamentos e gerencie o histórico.")

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Criar Novo Lançamento")
    
    col1, col2 = st.columns(2)
    with col1:
        data_input = st.date_input("Data do Lançamento", date.today())
        conta_id = st.number_input("ID da Conta (Razonete)", min_value=1, step=1)
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        grupo = st.selectbox(
            "Grupo", 
            ["Ativo", "Passivo", "Patrimônio Líquido", "Receitas", "Despesas", "Custos"]
        )
        
    with col2:
        operacao = st.selectbox("Operação", ["Débito", "Crédito"])
        status = st.selectbox(
            "Status Financeiro", 
            ["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]
        )
        justificativa = st.text_input("Justificativa", placeholder="Ex: Compra de mercadoria à vista")
        
    submit = st.form_submit_button("Confirmar e Gravar Lançamento")

    if submit:
        if not justificativa:
            st.warning("A justificativa é obrigatória!")
        elif not user_id:
            st.error("Erro ao identificar o utilizador. Por favor, inicie sessão novamente.")
        else:
            # Montando os dados EXATAMENTE de acordo com o seu SQL
            dados = {
                "user_id": user_id,
                "conta_id": conta_id,
                "operacao": operacao,
                "valor": valor if status in ["Entrada", "Investimento"] else -valor,
                "data_lancamento": str(data_input),
                "status_financeiro": status,
                "justificativa": justificativa,
                "grupo": grupo
            }
            
            try:
                supabase.table("lancamentos").insert(dados).execute()
                st.success("Lançamento registrado e processado com sucesso!")
                st.rerun() # Atualiza a tela para permitir novos lançamentos imediatamente
            except Exception as e:
                st.error(f"Erro ao salvar lançamento: {e}")

# --- HISTÓRICO DE LANÇAMENTOS ARMAZENADOS ---
st.markdown("---")
st.subheader("📊 Lançamentos Armazenados")

if user_id:
    try:
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
        
        if response.data:
            st.dataframe(response.data, use_container_width=True)
        else:
            st.info("Nenhum lançamento armazenado no histórico para este usuário.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
