import streamlit as st
import pandas as pd
import sys
import os

# Caminho absoluto para a raiz (Essencial para não dar erro de importação)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, inject_css, check_auth

st.set_page_config(layout="wide")
inject_css("style.css")

# Autenticação
user_id = check_auth()
supabase = get_supabase()

# Listas de Opções
LISTA_GRUPOS = [
    "Ativo Circulante", "Ativo Não Circulante", 
    "Passivo Circulante", "Passivo Não Circulante", 
    "Patrimônio Líquido", "Despesas", 
    "Encargos Financeiros", "Receita"
]
LISTA_STATUS = ["PAGO", "PENDENTE", "ENTRADA", "INVESTIMENTO", "TRANSAÇÃO INTERNA"]

st.title("💰 Gestão Financeira")

# --- BUSCA DE DADOS ---
# Sempre buscamos as contas atualizadas antes de desenhar o form
try:
    contas_res = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    lanc_res = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    
    contas_data = contas_res.data if contas_res.data else []
    lancamentos_data = lanc_res.data if lanc_res.data else []
except Exception as e:
    st.error(f"Erro ao conectar ao banco: {e}")
    contas_data = []
    lancamentos_data = []

# --- ABAS ---
aba1, aba2 = st.tabs(["➕ Novo Lançamento", "📋 Gerenciar Lançamentos"])

with aba1:
    st.subheader("Configuração de Conta")
    
    # Criar nova conta
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        nova_conta = st.text_input("Nome da nova conta (ex: Banco X, Dinheiro Vivo):")
    with col_c2:
        st.write("###") # Alinhamento visual
        if st.button("➕ Criar Conta"):
            if nova_conta:
                supabase.table("contas").insert({"nome": nova_conta, "user_id": user_id}).execute()
                st.success(f"Conta '{nova_conta}' criada!")
                st.rerun() # Recarrega a página para atualizar o selectbox
    
    st.divider()
    
    st.subheader("Registrar novo movimento")
    
    # Preparar lista de contas para o selectbox
    lista_contas = {c.get("nome"): c.get("id") for c in contas_data}
    
    with st.form("form_lanc"):
        nome_conta = st.selectbox("Escolha a Conta", list(lista_contas.keys()) if lista_contas else ["Nenhuma conta encontrada"])
        grupo = st.selectbox("Grupo Contábil", LISTA_GRUPOS)
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data")
        op = st.selectbox("Operação", ["CREDITO", "DEBITO"])
        status = st.selectbox("Status", LISTA_STATUS)
        just = st.text_input("Justificativa")
        
        if st.form_submit_button("Salvar Lançamento"):
            if not lista_contas:
                st.error("Por favor, crie uma conta primeiro!")
            else:
                supabase.table("lancamentos").insert({
                    "user_id": user_id,
                    "conta_id": lista_contas.get(nome_conta),
                    "grupo": grupo,
                    "valor": valor,
                    "data_lancamento": str(data),
                    "operacao": op,
                    "status_financeiro": status,
                    "justificativa": just
                }).execute()
                st.success("Lançamento salvo com sucesso!")
                st.rerun()

with aba2:
    if lancamentos_data:
        df = pd.DataFrame(lancamentos_data)
        df['Excluir'] = False
        
        # Ajuste para exibir nome da conta em vez de ID (se necessário)
        # Por enquanto mantemos assim para simplicidade
        cols = ['Excluir', 'grupo', 'operacao', 'valor', 'data_lancamento', 'status_financeiro', 'justificativa']
        df_exibicao = df[[c for c in cols if c in df.columns]]
        
        edited_df = st.data_editor(
            df_exibicao.set_index('id'),
            column_config={
                "Excluir": st.column_config.CheckboxColumn("Excluir", help="Marque para deletar"),
                "grupo": st.column_config.SelectboxColumn("Grupo", options=LISTA_GRUPOS),
                "status_financeiro": st.column_config.SelectboxColumn("Status", options=LISTA_STATUS),
                "operacao": st.column_config.SelectboxColumn("Operação", options=["CREDITO", "DEBITO"]),
                "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f")
            },
            use_container_width=True
        )

        if st.button("💾 Salvar Alterações e Processar Exclusões"):
            for id_lanc, row in edited_df.iterrows():
                if row['Excluir']:
                    supabase.table("lancamentos").delete().eq("id", id_lanc).execute()
                else:
                    supabase.table("lancamentos").update({
                        "grupo": row["grupo"],
                        "valor": float(row["valor"]),
                        "operacao": row["operacao"],
                        "status_financeiro": row["status_financeiro"],
                        "justificativa": row["justificativa"]
                    }).eq("id", id_lanc).execute()
            st.rerun()

        st.divider()
        with st.expander("⚠️ Zona de Perigo: Excluir TODOS os Lançamentos"):
            if st.button("CONFIRMAR EXCLUSÃO TOTAL"):
                supabase.table("lancamentos").delete().eq("user_id", user_id).execute()
                st.rerun()
    else:
        st.info("Nenhum lançamento encontrado.")
