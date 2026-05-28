import streamlit as st
import pandas as pd
import sys, os
from datetime import date
from utils import get_supabase, check_auth, show_auth_sidebar

# Configuração de caminhos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 1. Proteção de Autenticação
check_auth()
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor, faça login para acessar esta página.")
    st.stop()

supabase = get_supabase()
show_auth_sidebar(supabase)
user_id = st.session_state.user.id

st.title("💰 Lançamentos")

# Carregar Contas
res_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
dicionario_contas = {c['nome_conta']: c['id'] for c in res_contas.data}
lista_contas = ["-- Selecionar Conta --"] + list(dicionario_contas.keys())

opcoes_grupo = [
    "Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", 
    "Passivo Não Circulante", "Patrimônio Líquido", "Receitas", 
    "Despesas", "Encargos Financeiros", "Transação Interna"
]

# --- Formulário de Cadastro ---
with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Criar Novo Lançamento")
    c1, c2 = st.columns(2)
    with c1: 
        conta_sel = st.selectbox("Conta", lista_contas)
    with c2: 
        nova_conta = st.text_input("OU Criar Nova Conta")
    
    justificativa = st.text_input("Justificativa")
    
    c3, c4 = st.columns(2)
    with c3:
        data = st.date_input("Data", date.today())
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    with c4:
        operacao = st.selectbox("Operação", ["Débito", "Crédito"])
        grupo = st.selectbox("Grupo", opcoes_grupo)
        status = st.selectbox("Status", ["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"])
        
    if st.form_submit_button("Gravar"):
        conta_id = dicionario_contas.get(conta_sel)
        if not conta_id and nova_conta:
            res_nova = supabase.table("contas").insert({"user_id": user_id, "nome_conta": nova_conta, "grupo": grupo}).execute()
            conta_id = res_nova.data[0]['id']
        
        if conta_id:
            supabase.table("lancamentos").insert({
                "user_id": user_id, "conta_id": conta_id, "operacao": operacao, 
                "valor": float(abs(valor)), "data_lancamento": str(data), 
                "status_financeiro": status, "grupo": grupo, "justificativa": justificativa
            }).execute()
            st.rerun()

# --- Histórico e Edição ---
st.markdown("---")
st.subheader("📊 Histórico")

res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()

if res_lanc.data:
    df = pd.DataFrame(res_lanc.data)
    id_to_name = {v: k for k, v in dicionario_contas.items()}
    df["Conta"] = df["conta_id"].map(id_to_name)
    
    # Preparação dos dados
    df_exibicao = df[["id", "data_lancamento", "Conta", "valor", "justificativa", "operacao", "status_financeiro", "grupo"]].copy()
    df_exibicao["data_lancamento"] = pd.to_datetime(df_exibicao["data_lancamento"])
    df_exibicao["valor"] = df_exibicao["valor"].fillna(0.0)

    # Editor de dados
    edited_df = st.data_editor(
        df_exibicao, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
            "data_lancamento": st.column_config.DateColumn("Data"),
            "Conta": st.column_config.TextColumn("Conta", disabled=True),
            "operacao": st.column_config.SelectboxColumn("Operação", options=["Débito", "Crédito"]),
            "status_financeiro": st.column_config.SelectboxColumn("Status", options=["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]),
            "grupo": st.column_config.SelectboxColumn("Grupo", options=opcoes_grupo)
        }
    )

    if st.button("💾 Salvar Alterações"):
        for i, row in edited_df.iterrows():
            if not row.equals(df_exibicao.iloc[i]):
                supabase.table("lancamentos").update({
                    "valor": float(row["valor"]),
                    "justificativa": row["justificativa"],
                    "status_financeiro": row["status_financeiro"],
                    "operacao": row["operacao"],
                    "grupo": row["grupo"]
                }).eq("id", row["id"]).execute()
        st.success("Alterações salvas com sucesso!")
