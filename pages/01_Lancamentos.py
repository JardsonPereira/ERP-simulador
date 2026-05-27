import streamlit as st
import sys
import os
from datetime import date

# --- CONFIGURAÇÃO ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

user = check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)
user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)

opcoes_grupo = [
    "Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", 
    "Passivo Não Circulante", "Patrimônio Líquido", "Receitas", 
    "Despesas", "Transação Interna"
]

st.title("💰 Lançamentos nos Razonetes")

# --- CARREGAR CONTAS ---
lista_para_selectbox = ["-- Selecionar Conta Existente --"]
dicionario_contas = {}
if user_id:
    try:
        res = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
        for conta in res.data:
            dicionario_contas[conta["nome_conta"]] = conta["id"]
            lista_para_selectbox.append(conta["nome_conta"])
    except: pass

# --- FORMULÁRIO ---
with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Criar Novo Lançamento")
    col1, col2 = st.columns(2)
    with col1: conta_sel = st.selectbox("Conta", lista_para_selectbox)
    with col2: nova_conta = st.text_input("OU Criar Nova Conta", placeholder="Ex: Banco X")
    justificativa = st.text_input("Justificativa")
    
    c1, c2 = st.columns(2)
    with c1: 
        data = st.date_input("Data", date.today())
        valor = st.number_input("Valor (R$)", min_value=0.00, format="%.2f")
    with c2:
        operacao = st.selectbox("Operação", ["Débito", "Crédito"])
        grupo = st.selectbox("Grupo", opcoes_grupo)
        status = st.selectbox("Status", ["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"])
        
    if st.form_submit_button("Gravar Lançamento"):
        if (conta_sel == "-- Selecionar Conta Existente --" and not nova_conta) or not justificativa:
            st.warning("Preencha a conta e a justificativa!")
        else:
            try:
                conta_id = dicionario_contas[conta_sel] if not nova_conta else supabase.table("contas").insert({"user_id":user_id, "nome_conta":nova_conta, "grupo":grupo}).execute().data[0]["id"]
                supabase.table("lancamentos").insert({"user_id":user_id, "conta_id":conta_id, "operacao":operacao, "valor":abs(valor), "data_lancamento":str(data), "status_financeiro":status, "grupo":grupo, "justificativa":justificativa}).execute()
                st.success("Registrado!")
                st.rerun()
            except Exception as e: st.error(f"Erro ao salvar: {e}")

# --- HISTÓRICO COM EDIÇÃO RESTAURADA ---
st.markdown("---")
st.subheader("📊 Histórico")
if user_id:
    res = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
    if res.data:
        # Prepara dados para exibição
        id_para_nome = {v: k for k, v in dicionario_contas.items()}
        for item in res.data: 
            item.update({"Excluir": False, "Conta": id_para_nome.get(item["conta_id"], "N/A"), "valor": abs(float(item["valor"]))})
        
        # Tabela editável
        edit = st.data_editor(
            res.data, 
            use_container_width=True, 
            disabled=["id", "user_id", "conta_id", "Conta"], 
            column_order=["Excluir", "data_lancamento", "Conta", "justificativa", "operacao", "valor", "grupo", "status_financeiro"],
            column_config={
                "valor": st.column_config.NumberColumn("Valor (R$)", min_value=0.00, format="%.2f"),
                "data_lancamento": st.column_config.DateColumn("Data"),
                "Excluir": st.column_config.CheckboxColumn("🗑️", width="small")
            }
        )
        
        # Botões de ação
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Salvar Edições"):
                try:
                    for i, row in enumerate(edit):
                        # Verifica se houve alteração real
                        if row != res.data[i]:
                            # Tratamento de segurança para conversão de valores
                            val_limpo = abs(float(row["valor"] or 0))
                            supabase.table("lancamentos").update({
                                "valor": val_limpo, 
                                "operacao": row["operacao"], 
                                "grupo": row["grupo"], 
                                "justificativa": row["justificativa"]
                            }).eq("id", row["id"]).execute()
                    st.success("Alterações salvas!")
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
        with c2:
            if st.button("🗑️ Excluir Selecionados"):
                ids = [r["id"] for r in edit if r["Excluir"]]
                if ids:
                    supabase.table("lancamentos").delete().in_("id", ids).execute()
                    st.rerun()
