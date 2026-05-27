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

# --- CARREGAR CONTAS CADASTRADAS ---
lista_para_selectbox = []
dicionario_contas = {}

if user_id:
    try:
        # Busca apenas o ID e o nome_conta da tabela 'contas'
        resposta_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
        
        if resposta_contas.data:
            for conta in resposta_contas.data:
                # Usamos a coluna correta que vimos no seu print: 'nome_conta'
                nome_exibicao = conta["nome_conta"]
                
                # Mapeia o Nome da conta para o seu ID numérico real
                dicionario_contas[nome_exibicao] = conta["id"]
            
            lista_para_selectbox = list(dicionario_contas.keys())
    except Exception as e:
        st.error(f"Erro ao carregar lista de contas: {e}")

# --- FORMULÁRIO DE LANÇAMENTO ---
if not lista_para_selectbox:
    st.info("⚠️ Nenhuma conta/razonete localizado na sua tabela 'contas'. Cadastre uma conta primeiro para poder selecioná-la aqui.")
else:
    with st.form("lancamento_form", clear_on_submit=True):
        st.subheader("📝 Criar Novo Lançamento")
        
        nome_lancamento = st.text_input(
            "Nome do Lançamento", 
            placeholder="Ex: Compra de Mercadorias, Pagamento de Luz, etc."
        )

        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data do Lançamento", date.today())
            
            # AQUI ESTÁ: A lista bonita com o nome das suas contas!
            conta_escolhida = st.selectbox("Selecione a Conta (Razonete)", lista_para_selectbox)
            
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
                # Pega o ID correto e invisível com base no nome que você selecionou na tela
                id_real_da_conta = dicionario_contas[conta_escolhida]
                
                # Montando os dados para enviar para a tabela lancamentos
                dados = {
                    "user_id": user_id,
                    "conta_id": id_real_da_conta,  # Envia o ID correto para a Foreign Key
                    "operacao": operacao,
                    "valor": valor if status in ["Entrada", "Investimento"] else -valor,
                    "data_lancamento": str(data_input),
                    "status_financeiro": status,
                    "justificativa": nome_lancamento, 
                    "grupo": grupo
                }
                
                try:
                    supabase.table("lancamentos").insert(dados).execute()
                    st.success(f"Lançamento '{nome_lancamento}' registrado com sucesso na conta '{conta_escolhida}'!")
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
            st.dataframe(
                response.data, 
                use_container_width=True,
                column_config={
                    "id": None,          
                    "user_id": None,     
                    "conta_id": None,    
                    "justificativa": st.column_config.TextColumn("Nome do Lançamento", width="large")
                }
            )
        else:
            st.info("Nenhum lançamento armazenado.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
