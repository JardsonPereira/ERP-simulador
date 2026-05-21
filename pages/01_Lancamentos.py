import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, check_auth

# --- Configuração Inicial ---
check_auth()
supabase = get_supabase()

st.title("💰 Sistema de Gestão Financeira")

# --- Tabs de Navegação ---
tab_visualizar, tab_lancar, tab_contas = st.tabs(["📊 Ver Dados", "➕ Novo Lançamento", "🏦 Criar Conta"])

# --- Aba de Visualização ---
with tab_visualizar:
    st.subheader("Histórico de Lançamentos")
    
    lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
    contas = get_data_cached("contas", st.session_state.user.id)

    if lancamentos:
        df = pd.DataFrame(lancamentos)
        st.write("Dados de lançamentos:", df) # Útil para debug
        st.data_editor(df, use_container_width=True)
    else:
        st.info("Nenhum lançamento registrado.")

    st.divider()
    
    st.subheader("Contas Cadastradas")
    if contas:
        df_contas = pd.DataFrame(contas)
        # Debug para identificar os nomes das colunas reais
        # st.write("Colunas detectadas:", df_contas.columns.tolist()) 
        
        # Exibição segura (verifica se a coluna existe antes de tentar acessar)
        colunas_disponiveis = [c for c in ['nome_conta', 'tipo_conta'] if c in df_contas.columns]
        if colunas_disponiveis:
            st.table(df_contas[colunas_disponiveis])
        else:
            st.warning("As colunas 'nome_conta' ou 'tipo_conta' não foram encontradas. Verifique o seu banco de dados.")
            st.dataframe(df_contas)
    else:
        st.info("Nenhuma conta criada.")

# --- Aba de Novo Lançamento ---
with tab_lancar:
    st.subheader("Registrar Movimentação")
    if not contas:
        st.error("Você precisa criar uma conta antes de realizar um lançamento!")
    else:
        with st.form("form_novo_lancamento", clear_on_submit=True):
            lista_contas = {c['nome_conta']: c['id'] for c in contas}
            nome_conta = st.selectbox("Conta", options=list(lista_contas.keys()))
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            operacao = st.selectbox("Operação", ["Receita", "Despesa"])
            justificativa = st.text_input("Justificativa")
            
            if st.form_submit_button("Salvar Lançamento"):
                # Exemplo de inserção (ajuste conforme o método no seu utils.py)
                # supabase.table("lancamentos").insert({
                #     "conta_id": lista_contas[nome_conta],
                #     "valor": valor,
                #     "operacao": operacao,
                #     "justificativa": justificativa,
                #     "user_id": st.session_state.user.id
                # }).execute()
                st.success("Lançamento registrado!")
                st.rerun()

# --- Aba de Criar Conta ---
with tab_contas:
    st.subheader("Nova Conta")
    with st.form("form_nova_conta", clear_on_submit=True):
        nome = st.text_input("Nome da conta")
        tipo = st.selectbox("Tipo", ["Banco", "Dinheiro", "Cartão de Crédito"])
        
        if st.form_submit_button("Criar Conta"):
            # Lógica de inserção no Supabase aqui
            st.success(f"Conta '{nome}' criada!")
            st.rerun()
