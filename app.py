import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURAÇÃO ---
st.set_page_config(layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LÓGICA DE CONTABILIDADE E RELATÓRIOS ---
def gerar_balancete(df):
    st.subheader("🧾 Balancete de Verificação")
    st.table(df.groupby('natureza')['valor'].sum())

def gerar_dre(df):
    st.subheader("📈 DRE (Demonstrativo de Resultado)")
    receitas = df[df['natureza'] == 'Receitas']['valor'].sum()
    despesas = df[df['natureza'].isin(['CMV', 'Despesas'])]['valor'].sum()
    st.metric("Lucro Líquido", f"R$ {receitas - despesas:,.2f}")

def gerar_razonetes(df):
    st.subheader("📊 Razonetes")
    for natureza, grupo in df.groupby('natureza'):
        st.write(f"**Conta: {natureza}**")
        st.table(grupo[['descricao', 'tipo', 'valor']])

# --- TELAS ---
def mostrar_sistema(user_id, is_admin):
    # Carrega dados
    lanc = supabase.table("lancamentos").select("*").execute().data
    df = pd.DataFrame(lanc) if lanc else pd.DataFrame()

    menu = st.sidebar.radio("Navegação", ["🛒 Lançamentos", "📊 Razonetes", "🧾 Balancete", "📈 DRE", "⚙️ Admin"])

    if menu == "🛒 Lançamentos":
        st.header("Lançamentos Contábeis")
        with st.form("lanca"):
            desc = st.text_input("Descrição")
            nat = st.selectbox("Grupo", ["Ativo", "Passivo", "PL", "Receitas", "Despesas"])
            tipo = st.radio("Operação", ["Débito", "Crédito"])
            valor = st.number_input("Valor")
            if st.form_submit_button("Lançar"):
                supabase.table("lancamentos").insert({"descricao": desc, "natureza": nat, "tipo": tipo, "valor": valor, "user_id": user_id}).execute()
                st.rerun()
    elif menu == "📊 Razonetes": gerar_razonetes(df)
    elif menu == "🧾 Balancete": gerar_balancete(df)
    elif menu == "📈 DRE": gerar_dre(df)
    elif menu == "⚙️ Admin":
        if is_admin: st.write("Painel Administrativo: Gestão total.")
        else: st.error("Acesso Negado.")

# --- LOGIN ---
if not st.session_state.user:
    email = st.sidebar.text_input("E-mail")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state.user = res.user
        st.rerun()
else:
    is_admin = st.session_state.user.email == "seu-email@exemplo.com"
    mostrar_sistema(st.session_state.user.id, is_admin)
