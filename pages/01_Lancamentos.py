import streamlit as st
import pandas as pd
import sys, os
from datetime import date
from utils import get_supabase, check_auth, show_auth_sidebar

# Configuração
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)
user_id = st.session_state.user.id

st.title("💰 Lançamentos")

# Carregar Contas
res_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
dicionario_contas = {c['nome_conta']: c['id'] for c in res_contas.data}
lista_contas = ["-- Selecionar Conta --"] + list(dicionario_contas.keys())

# Grupos atualizados
opcoes_grupo = [
    "Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", 
    "Passivo Não Circulante", "Patrimônio Líquido", "Receitas", 
    "Despesas", "Encargos Financeiros", "Transação Interna"
]

with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Criar Novo Lançamento")
    c1, c2 = st.columns(2)
    with c1: conta_sel = st.selectbox("Conta", lista_contas)
    with c2: nova_conta = st.text_input("OU Criar Nova Conta")
    
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
                "valor": abs(valor), "data_lancamento": str(data), 
                "status_financeiro": status, "grupo": grupo, "justificativa": justificativa
            }).execute()
            st.rerun()

st.markdown("---")
st.subheader("📊 Histórico")
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()

if res_lanc.data:
    df = pd.DataFrame(res_lanc.data)
    df = df.loc[:, ~df.columns.duplicated()] # Limpeza de colunas duplicadas
    df["Excluir"] = False
    
    id_to_name = {v: k for k, v in dicionario_contas.items()}
    df["Conta"] = df["conta_id"].map(id_to_name)

    df_edit = df[["Excluir", "data_lancamento", "Conta", "valor", "justificativa", "operacao", "status_financeiro"]]

    edit = st.data_editor(
        df_edit, use_container_width=True,
        column_config={"valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"), "Excluir": st.column_config.CheckboxColumn("Excluir")}
    )

    if st.button("💾 Salvar/Excluir"):
        for i in range(len(edit)):
            if edit.iloc[i]["Excluir"]:
                supabase.table("lancamentos").delete().eq("id", df.iloc[i]["id"]).execute()
            elif not edit.iloc[i].equals(df_edit.iloc[i]):
                supabase.table("lancamentos").update({"valor": float(edit.iloc[i]["valor"]), "justificativa": edit.iloc[i]["justificativa"]}).eq("id", df.iloc[i]["id"]).execute()
        st.rerun()
