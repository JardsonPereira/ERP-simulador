import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth, show_auth_sidebar

# Configuração e Autenticação
check_auth()
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor, faça login para acessar esta página.")
    st.stop()

supabase = get_supabase()
show_auth_sidebar(supabase)
user_id = st.session_state.user.id

st.title("💰 Gestão Contábil: Lançamentos")

# Carregar Contas e Grupos
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()
contas_df = pd.DataFrame(res_contas.data)
lista_contas = ["-- Selecionar Conta --"] + (contas_df['nome_conta'].tolist() if not contas_df.empty else [])

# 1. Formulário de Cadastro (Partidas Dobradas)
with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Novo Lançamento (Partida Dobrada)")
    c1, c2 = st.columns(2)
    with c1:
        conta_deb = st.selectbox("Conta de Débito (Origem/Aumento de Ativo)", lista_contas)
    with c2:
        conta_cred = st.selectbox("Conta de Crédito (Destino/Origem de Recursos)", lista_contas)
    
    justificativa = st.text_input("Justificativa")
    c3, c4 = st.columns(2)
    with c3:
        data = st.date_input("Data", date.today())
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    with c4:
        st.info("A soma dos débitos deve igualar os créditos para manter o equilíbrio patrimonial.")
    
    if st.form_submit_button("Gravar Partida"):
        if conta_deb == "-- Selecionar Conta --" or conta_cred == "-- Selecionar Conta --":
            st.error("Selecione ambas as contas para completar a partida dobrada.")
        else:
            id_deb = contas_df[contas_df['nome_conta'] == conta_deb].iloc[0]['id']
            id_cred = contas_df[contas_df['nome_conta'] == conta_cred].iloc[0]['id']
            
            # Registro do Débito (Valor Positivo)
            supabase.table("lancamentos").insert({
                "user_id": user_id, "conta_id": id_deb, "valor": valor, 
                "operacao": "Débito", "data_lancamento": str(data), "justificativa": justificativa
            }).execute()
            
            # Registro do Crédito (Valor Negativo para fechar balancete)
            supabase.table("lancamentos").insert({
                "user_id": user_id, "conta_id": id_cred, "valor": -valor, 
                "operacao": "Crédito", "data_lancamento": str(data), "justificativa": justificativa
            }).execute()
            st.rerun()

# 2. Histórico e Balancete
st.markdown("---")
st.subheader("📊 Histórico e Balancete")

res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()

if res_lanc.data:
    df = pd.DataFrame(res_lanc.data)
    df["Conta"] = df["conta_id"].map(contas_df.set_index('id')['nome_conta'])
    
    # Exibição do Editor
    edited_df = st.data_editor(
        df[["id", "data_lancamento", "Conta", "valor", "operacao", "justificativa"]],
        use_container_width=True, hide_index=True
    )

    # Resumo do Balancete
    balancete = df.groupby("Conta")["valor"].sum().reset_index()
    total_balancete = balancete["valor"].sum()
    
    st.write("### Posição das Contas")
    st.dataframe(balancete, use_container_width=True)
    
    if abs(total_balancete) < 0.01:
        st.success(f"Balanço Fechado (Soma = 0). O patrimônio está equilibrado.")
    else:
        st.error(f"⚠️ Balanço Desequilibrado! Diferença: R$ {total_balancete:.2f}")
