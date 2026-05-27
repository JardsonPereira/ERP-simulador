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

# --- CARREGAR CONTAS CADASTRADAS (Para substituir o ID por uma lista de nomes) ---
lista_para_selectbox = []
dicionario_contas = {}

if user_id:
    try:
        # Busca todas as contas do usuário
        resposta_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
        
        if resposta_contas.data:
            for conta in resposta_contas.data:
                # Tentativa de descobrir qual coluna guarda o nome da conta (nome, descricao ou a própria ID)
                nome_exibicao = conta.get("nome") or conta.get("descricao") or f"Conta ID: {conta['id']}"
                
                # Mapeia o Nome que aparece na tela para a ID real que vai pro banco
                dicionario_contas[nome_exibicao] = conta["id"]
            
            lista_para_selectbox = list(dicionario_contas.keys())
    except Exception as e:
        st.error(f"Erro ao carregar lista de contas: {e}")

# --- FORMULÁRIO DE LANÇAMENTO ---
# Se o usuário não tiver contas criadas na tabela 'contas', avisa ele antes
if not lista_para_selectbox:
    st.info("⚠️ Nenhuma conta cadastrada localizada na tabela 'contas'. Cadastre uma conta primeiro para poder selecioná-la aqui.")
else:
    with st.form("lancamento_form", clear_on_submit=True):
        st.subheader("📝 Criar Novo Lançamento")
        
        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data do Lançamento", date.today())
            
            # AQUI: O campo de digitar ID foi retirado e substituído por uma lista visual das suas contas!
            conta_escolhida = st.selectbox("Selecione a Conta", lista_para_selectbox)
            
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
                # Resgata a ID numérica correspondente à conta selecionada pelo usuário
                id_real_da_conta = dicionario_contas[conta_escolhida]
                
                # Montando os dados EXATAMENTE de acordo com o seu SQL
                dados = {
                    "user_id": user_id,
                    "conta_id": id_real_da_conta, # Envia a ID correta por debaixo dos panos
                    "operacao": operacao,
                    "valor": valor if status in ["Entrada", "Investimento"] else -valor,
                    "data_lancamento": str(data_input),
                    "status_financeiro": status,
                    "justificativa": justificativa,
                    "grupo": group if 'group' in locals() else grupo
                }
                
                try:
                    supabase.table("lancamentos").insert(dados).execute()
                    st.success("Lançamento registrado e processado com sucesso!")
                    st.rerun() # Atualiza a tela limpando o formulário para receber o próximo lançamento
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
