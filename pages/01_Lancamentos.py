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
st.markdown("Efetue novos lançamentos de Débito e Crédito e gerencie o histórico.")

# --- CARREGAR CONTAS DISPONÍVEIS ---
# Buscando da tabela 'contas' que o próprio Supabase indicou no erro anterior
lista_contas = []
dicionario_contas = {}

if user_id:
    try:
        resposta_contas = supabase.table("contas").select("id", "nome").eq("user_id", user_id).execute()
        if resposta_contas.data:
            dicionario_contas = {item["nome"]: item["id"] for item in resposta_contas.data}
            lista_contas = list(dicionario_contas.keys())
    except Exception as e:
        st.error(f"Erro ao carregar contas do banco: {e}")

# --- FORMULÁRIO DE LANÇAMENTO ---
if not lista_contas:
    st.info("⚠️ Nenhuma conta/razonete localizado. Por favor, certifique-se de cadastrar uma conta primeiro na sua tabela 'contas'.")
else:
    with st.form("lancamento_form", clear_on_submit=True):
        st.subheader("📝 Criar Novo Lançamento")
        
        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data do Lançamento", date.today())
            conta_selecionada = st.selectbox("Selecione a Conta (Razonete)", lista_contas)
            valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
            
        with col2:
            # Atendendo ao pedido de Débito e Crédito
            tipo_contabil = st.selectbox("Operação Contábil", ["Débito", "Crédito"])
            
            # Atendendo aos novos status solicitados
            status = st.selectbox(
                "Status do Lançamento", 
                ["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]
            )
            
        # Atendendo à Justificativa do lançamento
        justificativa = st.text_input("Justificativa / Histórico da Operação", placeholder="Ex: Compra de mercadoria à vista")
        
        submit = st.form_submit_button("Confirmar e Gravar Lançamento")

        if submit:
            if not justificativa:
                st.warning("A justificativa/histórico é obrigatória!")
            elif not user_id:
                st.error("Erro ao identificar o utilizador. Por favor, inicie sessão novamente.")
            else:
                id_da_conta = dicionario_contas[conta_selecionada]
                
                # Montando os dados para bater com as colunas reais do seu banco
                dados = {
                    "user_id": user_id,
                    "data_lancamento": str(data_input),
                    "conta_id": id_da_conta,
                    # Combinamos o Débito/Crédito com a Justificativa para salvar no campo 'operacao' do banco
                    "operacao": f"[{tipo_contabil}] {justificativa}", 
                    "status_financeiro": status,
                    # Definindo se o valor entra positivo ou negativo dependendo do contexto contábil aplicado
                    "valor": valor if status in ["Entrada", "Investimento"] else -valor
                }
                
                try:
                    supabase.table("lancamentos").insert(dados).execute()
                    st.success("Lançamento registrado e processado com sucesso!")
                    st.rerun() # Atualiza a tela permitindo novos lançamentos imediatos
                except Exception as e:
                    st.error(f"Erro ao salvar lançamento: {e}")

# --- HISTÓRICO DE LANÇAMENTOS ARMAZENADOS ---
st.markdown("---")
st.subheader("📊 Lançamentos Armazenados")

if user_id:
    try:
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
        
        if response.data:
            # O st.dataframe permite visualizar e receber novos dados infinitamente em formato de planilha interativa
            st.dataframe(response.data, use_container_width=True)
        else:
            st.info("Nenhum lançamento armazenado no histórico para este usuário.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
