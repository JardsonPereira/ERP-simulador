import streamlit as st
import os
from supabase import create_client
from fpdf import FPDF

# --- CONEXÃO ---
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# --- AUTENTICAÇÃO ---
def check_auth():
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.switch_page("app.py")
        st.stop()
    return st.session_state["user"]

def show_auth_sidebar(supabase):
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        email = getattr(user, 'email', None) or (user.get('email') if isinstance(user, dict) else "Usuário")
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Logado como:** {email}")
        if st.sidebar.button("🚪 Deslogar"):
            supabase.auth.sign_out()
            st.session_state["user"] = None
            st.switch_page("app.py")
            st.rerun()

# --- DADOS ---
@st.cache_data
def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    res = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return res.data

# --- CSS E RELATÓRIOS ---
def inject_css():
    st.markdown("<style>.stMetric { background-color: #f9f9f9; padding: 10px; border-radius: 5px; }</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    for _, row in df.iterrows():
        texto = f"{str(row['data_lancamento'])[:10]} | {row.get('nome_conta', '')} | {row.get('status_financeiro', '')} | R$ {float(row.get('valor', 0)):,.2f}"
        pdf.cell(200, 10, txt=texto, ln=True)
    return pdf.output(dest='S').encode('latin-1')
