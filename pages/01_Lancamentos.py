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
    
    # Campo para você dar o nome/título ao lançamento
    nome_lancamento = st.text_input(
        "Nome do Lançamento", 
        placeholder="Ex: Compra de Mercadorias, Pagamento de Luz, etc."
    )

    col1, col2 = st.columns(2)
    with col1:
        data_input = st.date_input("Data do Lançamento", date.today())
        
        # AQUI: Retornamos ao campo de número simples. Sem listas confusas!
        conta_id = st.number_input("ID da Conta", min_value=1, step=1)
        
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        
    with col2:
        operacao = st.selectbox("Operação", ["Débito", "Crédito"])
        grupo = st.selectbox(
            "Grupo Contábil", 
            ["Ativo", "Passivo", "Patrimônio Líquido", "Receitas", "Despesas", "Custos"]
        )
        status = st.selectbox(
            "Status Financeiro", 
            ["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]
        )
        
    submit = st.form_submit_button("Confirmar e Gravar Lançamento")

    if submit:
        if not nome_lancamento:
            st.warning("O nome do lançamento é obrigatório!")
        elif not user_id:
            st.error("Sessão inválida. Faça login novamente.")
        else:
            # Montando os dados para enviar ao banco de dados
            dados = {
                "user_id": user_id,
                "conta_id": conta_id,  # Envia o número que você digitar diretamente
                "operacao": operacao,
                "valor": valor if status in ["Entrada", "Investimento"] else -valor,
                "data_lancamento": str(data_input),
                "status_financeiro": status,
                "justificativa": nome_lancamento, 
                "grupo": grupo
            }
            
            try:
                supabase.table("lancamentos").insert(dados).execute()
                st.success(f"Lançamento '{nome_lancamento}' registrado com sucesso!")
                st.rerun() 
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# --- HISTÓRICO DE LANÇAMENTOS ARMAZENADOS ---
st.markdown("---")
st.subheader("📊 Lançamentos Armazenados")

if user_id:
    try:
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
        
        if response.data:
            # Mostra a tabela e oculta apenas as colunas de ID internas que não importam na visualização
            st.dataframe(
                response.data, 
                use_container_width=True,
                column_config={
                    "id": None,          
                    "user_id": None,     
                    "justificativa": st.column_config.TextColumn("Nome do Lançamento", width="large")
                }
            )
        else:
            st.info("Nenhum lançamento armazenado.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
