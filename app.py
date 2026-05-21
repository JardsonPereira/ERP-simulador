import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="ERP Didático", layout="wide", page_icon="📊")

# --- CSS MODERNO ---
st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .t-account { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; margin-bottom: 15px; }
    .t-title { text-align: center; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; border-bottom: 2px solid #333; }
    .t-saldo { text-align: center; font-weight: bold; font-size: 1em; margin-top: 5px; border-top: 2px solid #333; color: #0056b3; }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÃO DE PDF CONSOLIDADO (MODELO SOLICITADO) ---
def gerar_relatorio_consolidado(usuario, periodo, df_fluxo, df_dre, df_balancete):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RELATÓRIO CONTÁBIL CONSOLIDADO", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Usuário: {usuario}", ln=True)
    pdf.cell(0, 8, f"Período: {periodo} | Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)

    # 1. Fluxo de Caixa
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. FLUXO DE CAIXA E VARIAÇÃO", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Saldo Inicial: R$ {df_fluxo['inicial']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo Final: R$ {df_fluxo['final']:,.2f}", ln=True)
    pdf.ln(5)

    # 2. DRE
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DEMONSTRAÇÃO DO RESULTADO (DRE)", ln=True)
    pdf.set_font("Arial", size=10)
    for index, row in df_dre.iterrows():
        pdf.cell(0, 8, f"{row['Descrição']} : R$ {row['Valor']:,.2f}", ln=True)
    pdf.ln(5)

    # 3. Balanço
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. BALANÇO PATRIMONIAL CONSOLIDADO", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 10, "ATIVO", border=1)
    pdf.cell(95, 10, "PASSIVO E PL", border=1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    # Simples renderização das linhas do balancete
    for index, row in df_balancete.iterrows():
        pdf.cell(95, 8, str(row.get('Ativo', '')), border=1)
        pdf.cell(95, 8, str(row.get('Passivo', '')), border=1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# --- AUTENTICAÇÃO ---
if 'user' not in st.session_state:
    st.title("🔐 Login / Cadastro")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    username = st.text_input("Nome de Usuário")
    col1, col2 = st.columns(2)
    if col1.button("Cadastrar"):
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            try:
                supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute()
                st.success("Conta criada! Faça login.")
            except Exception as e: st.error(f"Erro: {e}")
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e: st.error(f"Falha no login: {e}")
    st.stop()

# --- FUNÇÕES AUXILIARES ---
def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- INTERFACE PRINCIPAL ---
st.sidebar.title(f"🏢 ERP Didático")
st.sidebar.caption(f"Usuário: {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Fluxo de Caixa", "DRE", "Estoque"])

# --- LÓGICA DE RELATÓRIO NO SIDEBAR ---
if st.sidebar.button("Gerar Relatório Consolidado PDF"):
    # Re-processa dados para o relatório
    lanc = get_data("lancamentos")
    cont = get_data("contas")
    if lanc and cont:
        # Simplificação para o exemplo: você deve integrar seus cálculos de Fluxo/DRE/Balanço aqui
        st.download_button("Baixar Relatório Completo", 
                           data=gerar_relatorio_consolidado(
                               st.session_state.user.email, 
                               "Mês Atual", 
                               {'inicial': 0, 'final': 0}, # Dados do Fluxo
                               pd.DataFrame({"Descrição": ["Receita", "Despesa"], "Valor": [0, 0]}), # Dados da DRE
                               pd.DataFrame({"Ativo": ["Caixa"], "Passivo": ["Capital"]}) # Dados do Balanço
                           ), 
                           file_name="relatorio_contabil.pdf")
    else: st.warning("Dados insuficientes.")

# --- MANTENHA O RESTANTE DO CÓDIGO AQUI ---
# (Seu código original continua inalterado abaixo desta linha)
