import streamlit as st
import pandas as pd
from supabase import create_client

st.set_page_config(layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- FUNÇÕES DE LÓGICA E RELATÓRIOS ---
def gerar_relatorios(df):
    st.subheader("🧾 Balancete de Verificação")
    balancete = df.groupby('natureza')['valor'].sum()
    st.table(balancete)
    
    st.subheader("📈 DRE (Resumida)")
    receitas = df[df['natureza'] == 'Receitas']['valor'].sum()
    despesas = df[df['natureza'].isin(['CMV', 'Despesas'])]['valor'].sum()
    st.metric("Lucro Líquido", f"R$ {receitas - despesas:,.2f}")

# --- TELA DE CADASTROS/LANÇAMENTOS ---
def mostrar_sistema(user_id, is_admin):
    # Carrega dados do banco
    lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute().data
    df = pd.DataFrame(lanc) if lanc else pd.DataFrame()

    menu = st.sidebar.radio("Navegação", ["🛒 Lançamentos", "📊 Relatórios", "⚙️ Admin"])

    if menu == "🛒 Lançamentos":
        # (Seu código de Entrada/Saída aqui...)
        st.write("Registrar novas operações...")
        
    elif menu == "📊 Relatórios":
        if not df.empty:
            gerar_relatorios(df)
        else:
            st.info("Sem dados para relatórios.")
            
    elif menu == "⚙️ Admin":
        if is_admin:
            st.header("🛡️ Painel Administrativo")
            st.write("Gestão global de usuários e auditoria.")
        else:
            st.error("Acesso negado: Apenas administradores.")

# --- FLUXO PRINCIPAL ---
if not st.session_state.user:
    # ... (Login igual ao anterior) ...
    email = st.sidebar.text_input("E-mail")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state.user = res.user
        st.rerun()
else:
    # Verifica se é admin pelo e-mail
    is_admin = st.session_state.user.email == "seu-email-admin@exemplo.com"
    mostrar_sistema(st.session_state.user.id, is_admin)
