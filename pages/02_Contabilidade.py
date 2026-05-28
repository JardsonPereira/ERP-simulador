import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth, show_auth_sidebar

# 1. Configuração e Autenticação
check_auth()
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor, faça login.")
    st.stop()

supabase = get_supabase()
user_id = st.session_state.user.id

st.title("⚖️ Contabilidade Patrimonial")

# Carregar Contas
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()
contas_df = pd.DataFrame(res_contas.data)
lista_contas = ["-- Selecionar Conta --"] + (contas_df['nome_conta'].tolist() if not contas_df.empty else [])

# 2. Formulário de Partidas Dobradas
with st.form("lancamento_duplo", clear_on_submit=True):
    st.subheader("📝 Lançamento Contábil (Partida Dobrada)")
    c1, c2 = st.columns(2)
    
    with c1:
        conta_debito = st.selectbox("Conta de Débito (Origem/Aplicação)", lista_contas)
    with c2:
        conta_credito = st.selectbox("Conta de Crédito (Destino/Origem)", lista_contas)
    
    valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
    data = st.date_input("Data", date.today())
    justificativa = st.text_input("Histórico/Justificativa")

    if st.form_submit_button("Lançar Partida"):
        if conta_debito == "-- Selecionar Conta --" or conta_credito == "-- Selecionar Conta --":
            st.error("Selecione ambas as contas.")
        else:
            # Busca IDs
            id_deb = contas_df[contas_df['nome_conta'] == conta_debito].iloc[0]['id']
            id_cred = contas_df[contas_df['nome_conta'] == conta_credito].iloc[0]['id']
            
            # Insere Débito
            supabase.table("lancamentos").insert({
                "user_id": user_id, "conta_id": id_deb, "valor": valor, 
                "operacao": "Débito", "data_lancamento": str(data), "justificativa": justificativa
            }).execute()
            
            # Insere Crédito
            supabase.table("lancamentos").insert({
                "user_id": user_id, "conta_id": id_cred, "valor": -valor, 
                "operacao": "Crédito", "data_lancamento": str(data), "justificativa": justificativa
            }).execute()
            
            st.success("Lançamento realizado com sucesso!")

# 3. Balancete de Verificação
st.markdown("---")
st.subheader("📊 Balancete de Verificação")

res_lanc = supabase.table("lancamentos").select("conta_id, valor").eq("user_id", user_id).execute()
if res_lanc.data:
    df_lanc = pd.DataFrame(res_lanc.data)
    df_lanc['nome_conta'] = df_lanc['conta_id'].map(contas_df.set_index('id')['nome_conta'])
    balancete = df_lanc.groupby('nome_conta')['valor'].sum().reset_index()
    
    st.dataframe(balancete, use_container_width=True)
    
    total = balancete['valor'].sum()
    if abs(total) < 0.01:
        st.success("Balanço Fechado: A soma dos débitos e créditos é zero.")
    else:
        st.error(f"Balanço Desequilibrado! Diferença: R$ {total:.2f}")

# Exemplo de fluxo contábil visual
st.markdown("---")
