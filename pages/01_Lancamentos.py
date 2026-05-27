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
lista_para_selectbox = ["-- Selecionar Conta Existente --"]
dicionario_contas = {}

if user_id:
    try:
        # Busca o ID e o nome_conta da sua tabela de contas
        resposta_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
        
        if resposta_contas.data:
            for conta in resposta_contas.data:
                nome_exibicao = conta["nome_conta"]
                dicionario_contas[nome_exibicao] = conta["id"]
                lista_para_selectbox.append(nome_exibicao)
    except Exception as e:
        st.error(f"Erro ao carregar lista de contas: {e}")

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Criar Novo Lançamento")
    
    nome_lancamento = st.text_input(
        "Nome do Lançamento", 
        placeholder="Ex: Compra de Mercadorias, Pagamento de Luz, etc."
    )

    # Nova seção para a escolha ou criação da conta
    st.markdown("---")
    col_conta1, col_conta2 = st.columns(2)
    with col_conta1:
        conta_escolhida = st.selectbox("Selecione uma Conta Existente", lista_para_selectbox)
    with col_conta2:
        nova_conta_nome = st.text_input("OU Digite o nome para CRIAR uma Nova Conta", placeholder="Ex: Banco Inter, Caixa")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        data_input = st.date_input("Data do Lançamento", date.today())
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
        elif conta_escolhida == "-- Selecionar Conta Existente --" and not nova_conta_nome:
            st.warning("Você precisa selecionar uma conta existente OU digitar o nome de uma nova conta!")
        elif not user_id:
            st.error("Sessão inválida. Faça login novamente.")
        else:
            id_real_da_conta = None
            
            try:
                # LÓGICA: Se o usuário digitou uma nova conta, cadastra ela primeiro
                if nova_conta_nome.strip():
                    dados_nova_conta = {
                        "user_id": user_id,
                        "nome_conta": nova_conta_nome.strip(),
                        "grupo": grupo # Associa a conta ao mesmo grupo contábil selecionado
                    }
                    # Insere na tabela 'contas'
                    resultado_conta = supabase.table("contas").insert(dados_nova_conta).execute()
                    
                    if resultado_conta.data:
                        # Pega o ID que o banco acabou de gerar para essa nova conta
                        id_real_da_conta = resultado_conta.data[0]["id"]
                        st.info(f"Nova conta '{nova_conta_nome}' criada automaticamente!")
                else:
                    # Se não digitou uma nova conta, pega o ID da conta selecionada na lista
                    id_real_da_conta = dicionario_contas[conta_escolhida]

                # Se conseguimos um ID de conta válido, faz o lançamento
                if id_real_da_conta:
                    dados_lancamento = {
                        "user_id": user_id,
                        "conta_id": id_real_da_conta,
                        "operacao": operacao,
                        "valor": valor if status in ["Entrada", "Investimento"] else -valor,
                        "data_lancamento": str(data_input),
                        "status_financeiro": status,
                        "justificativa": nome_lancamento, 
                        "grupo": grupo
                    }
                    
                    supabase.table("lancamentos").insert(dados_lancamento).execute()
                    st.success(f"Lançamento '{nome_lancamento}' registrado com sucesso!")
                    st.rerun() 
                    
            except Exception as e:
                st.error(f"Erro ao processar operação: {e}")

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
                    "conta_id": st.column_config.NumberColumn("ID da Conta"),    
                    "justificativa": st.column_config.TextColumn("Nome do Lançamento", width="large")
                }
            )
        else:
            st.info("Nenhum lançamento armazenado.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
