import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Didático 2026", layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# Inicializa sessão de usuário
if 'user' not in st.session_state:
    st.session_state.user = None

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

# --- TELA DO SISTEMA ---
def mostrar_sistema(user_id, email_usuario):
    # Carrega dados do Supabase
    lanc = supabase.table("lancamentos").select("*").execute().data
    df = pd.DataFrame(lanc) if lanc else pd.DataFrame()

    menu = st.sidebar.radio("Navegação", ["🛒 Lançamentos", "📊 Razonetes", "🧾 Balancete", "📈 DRE", "⚙️ Admin"])

    if menu == "🛒 Lançamentos":
        st.header("Lançamentos Contábeis")
        with st.form("lanca"):
            desc = st.text_input("Descrição")
            nat = st.selectbox("Grupo", ["Ativo", "Passivo", "PL", "Receitas", "Despesas", "CMV"])
            tipo = st.radio("Operação", ["Débito", "Crédito"])
            valor = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Lançar"):
                supabase.table("lancamentos").insert({
                    "descricao": desc, "natureza": nat, "tipo": tipo, "valor": valor, "user_email": email_usuario
                }).execute()
                st.rerun()
    elif menu == "📊 Razonetes": gerar_razonetes(df)
    elif menu == "🧾 Balancete": gerar_balancete(df)
    elif menu == "📈 DRE": gerar_dre(df)
    elif menu == "⚙️ Admin":
        # Verificação simples de admin
        if email_usuario == "seu-email@exemplo.com":
            st.write("Painel Administrativo: Gestão total.")
        else:
            st.error("Acesso Negado.")

# --- LOGIN E FLUXO PRINCIPAL ---
if not st.session_state.user:
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("E-mail")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.sidebar.error("E-mail ou senha inválidos.")
else:
    st.sidebar.write(f"Logado como: {st.session_state.user.email}")
    if st.sidebar.button("Sair"):
        st.session_state.user = None
        st.rerun()
    mostrar_sistema(st.session_state.user.id, st.session_state.user.email)
