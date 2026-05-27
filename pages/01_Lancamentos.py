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
st.markdown("Registre as movimentações de Débito e Crédito para compor os razonetes.")

# --- BUSCAR AS CONTAS CONTÁBEIS DO BANCO ---
lista_contas = []
dicionario_contas = {}

if user_id:
    try:
        # Busca as contas contábeis criadas pelo usuário para listar no formulário
        resposta_contas = supabase.table("contas_contabeis").select("id", "nome").eq("user_id", user_id).execute()
        if resposta_contas.data:
            # Cria um dicionário mapeando 'Nome da Conta' -> 'ID da Conta'
            dicionario_contas = {item["nome"]: item["id"] for item in resposta_contas.data}
            lista_contas = list(dicionario_contas.keys())
    except Exception as e:
        st.error(f"Erro ao carregar plano de contas: {e}")

# --- FORMULÁRIO DE LANÇAMENTO ---
if not lista_contas:
    st.info("⚠️ Antes de realizar um lançamento, você precisa cadastrar suas contas na aba de Plano de Contas (Razonetes).")
else:
    with st.form("lancamento_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_input = st.date_input("Data do Lançamento", date.today())
            conta_selecionada = st.selectbox("Selecione a Conta (Razonete)", lista_contas)
            valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        with col2:
            tipo_operacao = st.selectbox("Tipo de Operação", ["Débito", "Crédito"])
            descricao = st.text_input("Histórico / Descrição", placeholder="Ex: Integralização de Capital, Compra de Mercadorias")
        
        submit = st.form_submit_button("Gravar Lançamento")

        if submit:
            if not descricao:
                st.warning("A descrição/histórico é obrigatória!")
            elif not user_id:
                st.error("Erro ao identificar o utilizador. Por favor, inicie sessão novamente.")
            else:
                # Pega o ID correto da conta selecionada usando o dicionário
                id_da_conta = dicionario_contas[conta_selecionada]
                
                dados = {
                    "user_id": user_id,
                    "data_lancamento": str(data_input),
                    "conta_id": id_da_conta, # Vincula o lançamento ao ID do Razonete
                    "descricao": descricao,
                    "tipo": tipo_operacao,   # Salva se foi Débito ou Crédito
                    "valor": valor
                }
                try:
                    supabase.table("lancamentos").insert(dados).execute()
                    st.success("Lançamento registrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao guardar lançamento: {e}")

# --- LISTAGEM (HISTÓRICO) ---
st.subheader("Histórico de Lançamentos")

if user_id:
    try:
        # Busca os lançamentos trazendo os dados mais recentes primeiro
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
        
        if response.data:
            st.dataframe(response.data, use_container_width=True)
        else:
            st.info("Nenhum lançamento encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
