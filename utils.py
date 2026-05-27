import streamlit as st
import os
from supabase import create_client
from fpdf import FPDF

# --- CONEXÃO SUPABASE ---
def get_supabase():
    """Retorna a instância do cliente Supabase usando segredos."""
    return create_client(
        st.secrets["https://ejdvfuczdnpyhuosruey.supabase.co"], 
        st.secrets["sb_publishable_6x5uVjXcIh4KnlpQSFOv_g_P6rnEw08"]
    )

# --- AUTENTICAÇÃO ---
def check_auth():
    """Verifica se existe um usuário no session_state. Se não, redireciona."""
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.switch_page("app.py")
        st.stop()
    return st.session_state["user"]

def show_auth_sidebar(supabase):
    """Exibe o status do usuário logado e o botão de logout na sidebar."""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        email = getattr(user, 'email', None) or (user.get('email') if isinstance(user, dict) else "Usuário")
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Logado:**")
        st.sidebar.caption(email)
        
        if st.sidebar.button("🚪 Deslogar"):
            supabase.auth.sign_out()
            st.session_state["user"] = None
            st.switch_page("app.py")
            st.rerun()

# --- DADOS E CACHE ---
@st.cache_data
def get_data_cached(tabela, user_id):
    """Busca dados de uma tabela no Supabase com cache."""
    supabase = get_supabase()
    res = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return res.data

# --- ESTILIZAÇÃO E RELATÓRIOS ---
def inject_css(file_name="style.css"):
    """Lê um arquivo CSS e aplica ao Streamlit."""
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # CSS padrão caso o arquivo não exista
        st.markdown("<style>.stMetric { background-color: #f9f9f9; padding: 10px; border-radius: 5px; }</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, df):
    """Gera um PDF simples com os dados do DataFrame."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    
    # Cabeçalho da tabela no PDF
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(40, 10, "Data", border=1)
    pdf.cell(60, 10, "Conta", border=1)
    pdf.cell(40, 10, "Status", border=1)
    pdf.cell(30, 10, "Valor", border=1)
    pdf.ln()
    
    # Linhas
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        pdf.cell(40, 10, str(row['data_lancamento'].date()), border=1)
        pdf.cell(60, 10, str(row['nome_conta']), border=1)
        pdf.cell(40, 10, str(row['status_financeiro']), border=1)
        pdf.cell(30, 10, f"R$ {row['valor']:.2f}", border=1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')
