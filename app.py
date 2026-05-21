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

# --- FUNÇÃO DE PDF CONSOLIDADO (USANDO DADOS REAIS) ---
def gerar_relatorio_completo(usuario, df_dre, saldo_inicial, saldo_final, df_balancete):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RELATÓRIO CONTÁBIL CONSOLIDADO", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Usuário: {usuario}", ln=True)
    pdf.cell(0, 8, f"Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)

    # 1. Fluxo de Caixa
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. FLUXO DE CAIXA E VARIAÇÃO", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Saldo Inicial Acumulado: R$ {saldo_inicial:,.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo Final no Período: R$ {saldo_final:,.2f}", ln=True)
    pdf.ln(5)

    # 2. DRE
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DEMONSTRAÇÃO DO RESULTADO (DRE)", ln=True)
    pdf.set_font("Arial", size=10)
    for _, row in df_dre.iterrows():
        pdf.cell(0, 8, f"{row['Descrição']}: R$ {row['Valor']:,.2f}", ln=True)
    pdf.ln(5)

    # 3. Balanço
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. BALANÇO PATRIMONIAL CONSOLIDADO", ln=True)
    pdf.set_font("Arial", size=10)
    # Tabela simples do balancete
    for _, row in df_balancete.iterrows():
        pdf.cell(0, 8, f"{row.iloc[0]} | Valor: R$ {row.iloc[1]:,.2f}", ln=True)

    return pdf.output(dest='S').encode('latin-1')

# --- AUTENTICAÇÃO E FUNÇÕES AUXILIARES ---
if 'user' not in st.session_state:
    # (Mantido igual ao seu código original)
    st.title("🔐 Login / Cadastro")
    email = st.text_input("Email"); password = st.text_input("Senha", type="password"); username = st.text_input("Nome de Usuário")
    col1, col2 = st.columns(2)
    if col1.button("Cadastrar"):
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute(); st.success("Conta criada!")
    if col2.button("Entrar"):
        res = supabase.auth.sign_in_with_password({"email": email, "password": password}); st.session_state.user = res.user; st.rerun()
    st.stop()

def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- INTERFACE E BOTÃO DE RELATÓRIO NO SIDEBAR ---
st.sidebar.title(f"🏢 ERP Didático")
st.sidebar.caption(f"Usuário: {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Fluxo de Caixa", "DRE", "Estoque"])

# --- LÓGICA DE GERAÇÃO DO RELATÓRIO (USANDO VARIÁVEIS REAIS) ---
if st.sidebar.button("📄 Baixar Relatório Completo"):
    lanc = get_data("lancamentos")
    cont = get_data("contas")
    if lanc and cont:
        # Reprocessamento interno para garantir que os dados do PDF sejam atuais
        df = pd.DataFrame(lanc).merge(pd.DataFrame(cont), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        
        # Cálculos de Fluxo
        df_fc = df[df['status_financeiro'].isin(['ENTRADA', 'PAGO'])].copy()
        df_fc['fluxo'] = df_fc.apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else -x['valor'], axis=1)
        s_inicial = 0 # Valor base
        s_final = df_fc['fluxo'].sum()
        
        # Cálculos de DRE
        df_dre = df[df['grupo'].isin(['RECEITAS', 'DESPESAS', 'CMV', 'ENCARGOS FINANCEIROS'])]
        dre_res = pd.DataFrame({
            "Descrição": ["Receita", "CMV", "Despesas", "Lucro Líquido"],
            "Valor": [df_dre[df_dre['grupo']=='RECEITAS']['valor'].sum(), 
                      df_dre[df_dre['grupo']=='CMV']['valor'].sum(),
                      df_dre[df_dre['grupo']=='DESPESAS']['valor'].sum(),
                      (df_dre[df_dre['grupo']=='RECEITAS']['valor'].sum() - df_dre[df_dre['grupo']=='CMV']['valor'].sum() - df_dre[df_dre['grupo']=='DESPESAS']['valor'].sum())]
        })
        
        # Gerar PDF com variáveis reais
        pdf_data = gerar_relatorio_completo(st.session_state.user.email, dre_res, s_inicial, s_final, df[['nome_conta', 'valor']].head(5))
        st.download_button("Clique para baixar", data=pdf_data, file_name="relatorio_consolidado.pdf")
    else:
        st.error("Dados insuficientes para gerar relatório.")

# --- MANTENHA O RESTANTE DO SEU CÓDIGO AQUI (ABAS DRE, FLUXO, ETC.) ---
