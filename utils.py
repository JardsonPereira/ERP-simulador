import streamlit as st
import os
from supabase import create_client

# Inicialização do Cliente Supabase
def get_supabase():
    """Retorna a instância do cliente Supabase usando segredos."""
    return create_client(
        st.secrets["SUPABASE_URL"], import streamlit as st
from fpdf import FPDF

# Garanta que esta função de conexão esteja aqui
def get_supabase():
    from supabase import create_client
    # Substitua pelas suas credenciais ou mantenha a sua lógica atual
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def check_auth():
    if 'user' not in st.session_state:
        st.warning("Por favor, faça login.")
        st.stop()

def show_auth_sidebar(supabase):
    st.sidebar.write(f"Usuário: {st.session_state.user.email}")

@st.cache_data
def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    res = supabase.table(tabela).select("*").eq("user_id", user_id).execute()
    return res.data

def inject_css():
    st.markdown("<style>.stMetric { background-color: #f9f9f9; padding: 10px; border-radius: 5px; }</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        texto = f"{row['data_lancamento']} | {row['nome_conta']} | {row['status_financeiro']} | R$ {row['valor']:.2f}"
        pdf.cell(200, 10, txt=texto, ln=True)
    return pdf.output(dest='S').encode('latin-1')
        st.secrets["SUPABASE_KEY"]
    )

# Verificação de Autenticação
def check_auth():
    """
    Verifica se existe um usuário no session_state.
    Se não, redireciona para a página principal (login).
    """
    if "user" not in st.session_state or st.session_state["user"] is None:
        st.switch_page("app.py")
        st.stop()
    return st.session_state["user"]

# Sidebar de Autenticação
def show_auth_sidebar(supabase):
    """Exibe o status do usuário logado e o botão de logout na sidebar."""
    if "user" in st.session_state and st.session_state["user"]:
        user = st.session_state["user"]
        
        # Lida com o objeto user sendo um objeto ou dicionário
        email = getattr(user, 'email', None) or (user.get('email') if isinstance(user, dict) else "Usuário")
        
        st.sidebar.markdown("---")
        st.sidebar.write(f"👤 **Logado como:**")
        st.sidebar.caption(email)
        
        if st.sidebar.button("🚪 Deslogar"):
            supabase.auth.sign_out()
            st.session_state["user"] = None
            st.switch_page("app.py")
            st.rerun()

# Injeção de CSS
def inject_css(file_name="style.css"):
    """Lê um arquivo CSS e aplica ao Streamlit."""
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
