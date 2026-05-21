import streamlit as st
import pandas as pd
from utils import get_supabase, get_data_cached, check_auth

check_auth()
supabase = get_supabase()

st.title("💰 Sistema de Gestão Financeira")

tab_visualizar, tab_lancar, tab_contas = st.tabs(["📊 Ver Dados", "➕ Novo Lançamento", "🏦 Criar Conta"])

# --- 1. VISUALIZAÇÃO E EDIÇÃO ---
with tab_visualizar:
    st.subheader("Histórico de Lançamentos")
    lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
    contas = get_data_cached("contas", st.session_state.user.id)

    if lancamentos:
        df = pd.DataFrame(lancamentos)
        
        # Editor interativo: Permite editar e remover linhas
        # Obs: Você precisará tratar o envio das mudanças para o Supabase
        df_editado = st.data_editor(
            df,
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
            },
            use_container_width=True
        )
    else:
        st.info("Nenhum lançamento registrado.")

    st.divider()
    st.subheader("Contas Cadastradas")
    if contas:
        df_contas = pd.DataFrame(contas)
        st.table(df_contas[['nome_conta', 'tipo_conta']]) # Ajuste conforme as colunas do seu banco
    else:
        st.info("Nenhuma conta criada.")

# --- 2. NOVO LANÇAMENTO ---
with tab_lancar:
    with st.form("form_novo_lancamento"):
        conta_selecionada = st.selectbox("Conta", options=[c['nome_conta'] for c in contas])
        valor = st.number_input("Valor", min_value=0.0)
        operacao = st.selectbox("Operação", ["Receita", "Despesa"])
        justificativa = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            # AQUI: chame sua função de inserção no Supabase
            st.success("Lançamento registrado!")

# --- 3. CRIAR CONTA ---
with tab_contas:
    with st.form("form_nova_conta"):
        nome = st.text_input("Nome da nova conta (ex: Nubank, Carteira)")
        tipo = st.selectbox("Tipo", ["Banco", "Dinheiro", "Cartão de Crédito"])
        
        if st.form_submit_button("Criar Conta"):
            # AQUI: chame sua função de inserção no Supabase
            st.success(f"Conta '{nome}' criada com sucesso!")
