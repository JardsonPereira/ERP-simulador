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

# --- DADOS (CORRIGIDO PARA FLUXO DE CAIXA) ---
@st.cache_data(ttl=60) 
def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    res = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    
    # Normalização rigorosa: garante que a data seja sempre YYYY-MM-DD, sem fuso horário
    data = res.data
    for item in data:
        if 'data_lancamento' in item and item['data_lancamento']:
            # Corta a string em 10 caracteres (YYYY-MM-DD) para ignorar horas/fusos
            item['data_lancamento'] = str(item['data_lancamento'])[:10]
            
    return data

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
        # A data aqui já vem normalizada pela função de cima
        texto = f"{row['data_lancamento']} | {row.get('nome_conta', '')} | {row.get('status_financeiro', '')} | R$ {float(row.get('valor', 0)):,.2f}"
        pdf.cell(200, 10, txt=texto, ln=True)
    return pdf.output(dest='S').encode('latin-1')
