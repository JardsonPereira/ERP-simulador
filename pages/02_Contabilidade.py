import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth, show_auth_sidebar

# --- Configuração ---
check_auth()
if "user" not in st.session_state or st.session_state.user is None:
    st.warning("Por favor, faça login.")
    st.stop()

supabase = get_supabase()
user_id = st.session_state.user.id

st.set_page_config(page_title="Sistema Contábil", layout="wide")
st.title("⚖️ Sistema Contábil Patrimonial")

# --- Dados ---
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()
contas_df = pd.DataFrame(res_contas.data)
lista_contas = ["-- Selecionar --"] + (contas_df['nome_conta'].tolist() if not contas_df.empty else [])

# --- 1. Lançamentos (Partidas Dobradas) ---
with st.expander("📝 Criar Novo Lançamento (Partida Dobrada)", expanded=True):
    with st.form("lanc_dobrado"):
        c1, c2, c3 = st.columns(3)
        with c1: conta_deb = st.selectbox("Conta Débito (Origem/Aplicação)", lista_contas)
        with c2: conta_cred = st.selectbox("Conta Crédito (Destino/Origem)", lista_contas)
        with c3: valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        
        hist = st.text_input("Histórico")
        data = st.date_input("Data", date.today())
        
        if st.form_submit_button("Lançar"):
            if conta_deb == "-- Selecionar --" or conta_cred == "-- Selecionar --":
                st.error("Selecione ambas as contas!")
            else:
                id_deb = contas_df[contas_df['nome_conta'] == conta_deb].iloc[0]['id']
                id_cred = contas_df[contas_df['nome_conta'] == conta_cred].iloc[0]['id']
                
                # Inserir as duas pernas (Debito + / Credito -)
                supabase.table("lancamentos").insert([
                    {"user_id": user_id, "conta_id": id_deb, "valor": valor, "operacao": "Débito", "data_lancamento": str(data), "justificativa": hist},
                    {"user_id": user_id, "conta_id": id_cred, "valor": -valor, "operacao": "Crédito", "data_lancamento": str(data), "justificativa": hist}
                ]).execute()
                st.rerun()

# --- 2. Processamento Contábil ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
if res_lanc.data:
    df = pd.DataFrame(res_lanc.data)
    df["Conta"] = df["conta_id"].map(contas_df.set_index('id')['nome_conta'])
    df["Grupo"] = df["conta_id"].map(contas_df.set_index('id')['grupo'])

    # --- Razonetes ---
    st.subheader("📖 Razonetes (Saldos por Conta)")
    razonetes = df.groupby(["Conta", "Grupo"])["valor"].sum().reset_index()
    st.dataframe(razonetes, use_container_width=True)

    # --- Balancete ---
    st.subheader("⚖️ Balancete de Verificação")
    total_balancete = razonetes["valor"].sum()
    st.metric("Soma Total das Contas", f"R$ {total_balancete:,.2f}")
    if abs(total_balancete) < 0.01: st.success("Balanço Equilibrado!")
    else: st.error("Diferença encontrada no Balanço!")

    # --- Balanço Patrimonial ---
    st.subheader("📑 Balanço Patrimonial")
    col_a, col_p = st.columns(2)
    
    # Filtro Ativo vs Passivo/PL
    ativos = razonetes[razonetes["Grupo"].str.contains("Ativo", na=False)]
    passivos = razonetes[razonetes["Grupo"].str.contains("Passivo|Patrimônio", na=False)]
    
    with col_a:
        st.write("### ATIVO (Aplicação)")
        st.dataframe(ativos[["Conta", "valor"]], use_container_width=True)
        st.write(f"**TOTAL ATIVO: R$ {ativos['valor'].sum():,.2f}**")
        
    with col_p:
        st.write("### PASSIVO + PL (Origem)")
        # Inverter sinal para exibição contábil positiva
        passivos_disp = passivos.copy()
        passivos_disp["valor"] = passivos_disp["valor"].abs()
        st.dataframe(passivos_disp[["Conta", "valor"]], use_container_width=True)
        st.write(f"**TOTAL PASSIVO + PL: R$ {passivos_disp['valor'].sum():,.2f}**")
else:
    st.info("Nenhum lançamento encontrado.")
