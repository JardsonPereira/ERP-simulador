# Adicione isto ao final do seu utils.py
from fpdf import FPDF
import io

def get_data_cached(tabela, user_id):
    supabase = get_supabase()
    return supabase.table(tabela).select("*").eq("user_id", user_id).execute().data

def inject_css():
    st.markdown("<style>/* Seu estilo opcional */</style>", unsafe_allow_html=True)

def gerar_relatorio_pdf(titulo, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    for _, row in df.iterrows():
        texto = f"{row['data_lancamento'].date()} | {row['nome_conta']} | {row['status_financeiro']} | R$ {row['valor']:.2f}"
        pdf.cell(200, 10, txt=texto, ln=True)
    return pdf.output(dest='S').encode('latin-1')
