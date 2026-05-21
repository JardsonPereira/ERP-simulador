import streamlit as st
import os
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from fpdf import FPDF

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- CONEXÃO COM O SUPABASE ---
def get_supabase():
    """Retorna o cliente do Supabase configurado."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("Erro: Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não encontradas.")
        st.stop()
    return create_client(url, key)

# --- CACHE E BUSCA DE DADOS ---
@st.cache_data(ttl=600)
def get_data_cached(table, user_id):
    """Busca dados de forma cacheada para performance."""
    supabase = get_supabase()
    return supabase.table(table).select("*").eq("user_id", user_id).execute().data

# --- AUTENTICAÇÃO ---
def check_auth():
    """Verifica se o usuário está logado, caso contrário, para a execução."""
    if 'user' not in st.session_state:
        st.warning("⚠️ Por favor, faça o login na página inicial (Home).")
        st.stop()

# --- CSS E UI ---
def inject_css():
    """Injeta o estilo CSS moderno no app."""
    st.markdown("""
    <style>
        .stApp { background-color: #f4f7f6; }
        .card { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .t-account { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; margin-bottom: 15px; }
        .t-title { text-align: center; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; border-bottom: 2px solid #333; }
        .t-saldo { text-align: center; font-weight: bold; font-size: 1em; margin-top: 5px; border-top: 2px solid #333; color: #0056b3; }
    </style>
    """, unsafe_allow_html=True)

# --- GERAÇÃO DE PDF ---
def gerar_relatorio_pdf(titulo, df):
    """Gera um PDF básico a partir de um DataFrame."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "RELATÓRIO CONTÁBIL CONSOLIDADO", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, titulo, ln=True)
    pdf.set_font("Arial", size=10)
    
    # Tabela dinâmica
    col_width = 190 / len(df.columns)
    for col in df.columns: 
        pdf.cell(col_width, 10, str(col), border=1, align='C')
    pdf.ln()
    for _, row in df.iterrows():
        for val in row: 
            pdf.cell(col_width, 10, str(val), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')
