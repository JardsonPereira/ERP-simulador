import streamlit as st
import pandas as pd
import sys
import os

# Ajuste de caminho (isso faz o Python achar o utils.py que está na pasta raiz)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

st.set_page_config(layout="wide")
inject_css("style.css")

user_id = check_auth()
supabase = get_supabase()

st.title("💰 Gestão Financeira")

# --- BUSCA DE CONTAS E DADOS ---
# Buscamos as contas do banco de dados do usuário logado
try:
    contas_res = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    contas_data = contas_res.data if contas_res.data else []
except:
    contas_data = []

# Criamos um mapa para facilitar: { "Nome da Conta": "ID_DA_CONTA" }
lista_contas = {c.get("nome", "Sem Nome"): c.get("id") for c in contas_data}

# --- ABAS ---
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

with aba1:
    st.subheader("Registrar novo movimento")
    
    # Exibe o seletor de contas
    col_a, col_b = st.columns([2, 1])
    with col_a:
        # Se não houver contas, avisamos o usuário
        if lista_contas:
            nome_conta_selecionada = st.selectbox("Selecione a Conta", list(lista_contas.keys()))
        else:
            st.warning("Nenhuma conta encontrada. Crie uma ao lado.")
            nome_conta_selecionada = None
            
    with col_b:
        nova_conta = st.text_input("Criar nova conta:")
        if st.button("Adicionar Conta"):
            if nova_conta:
                supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
                st.rerun() # Atualiza para mostrar a nova conta na lista

    # Formulário de Lançamento
    with st.form("form_lancamento"):
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", ["PAGO", "PENDENTE"])
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            if not nome_conta_selecionada:
                st.error("Por favor, selecione ou crie uma conta primeiro.")
            else:
                # Pegamos o ID real baseado no nome selecionado
                conta_id = lista_contas.get(nome_conta_selecionada)
                
                supabase.table("lancamentos").insert({
                    "user_id": user_id,
                    "conta_id": conta_id, # Enviamos o ID correto
                    "valor": valor,
                    "data_lancamento": str(data),
                    "operacao": op,
                    "status_financeiro": status,
                    "justificativa": just
                }).execute()
                st.success("Lançamento salvo com sucesso!")

with aba2:
    st.write("Aqui viria a lista de lançamentos (use o mesmo df_editavel dos exemplos anteriores).")
