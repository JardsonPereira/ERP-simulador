import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
from fpdf import FPDF
from datetime import datetime

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

# --- FUNÇÃO PDF ---
def gerar_relatorio_pdf(user_name, dre, bal, fluxo, lanc):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Relatório Contábil Consolidado", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Usuário: {user_name} | {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    def add_section(titulo, df):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, titulo, ln=True)
        pdf.set_font("Arial", size=8)
        for _, row in df.head(20).iterrows():
            pdf.cell(0, 6, " | ".join([str(v) for v in row.values])[:100], border=1, ln=True)
        pdf.ln(5)
        
    add_section("DRE", dre)
    add_section("Balancete", bal)
    add_section("Fluxo de Caixa", fluxo[['data_lancamento', 'nome_conta', 'valor']])
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
            supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute()
            st.success("Conta criada!"); st.rerun()
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e: st.error(f"Falha: {e}")
    st.stop()

# --- FUNÇÕES ---
def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- INTERFACE ---
st.sidebar.title("🏢 ERP Didático")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Fluxo de Caixa", "DRE", "Estoque", "Relatórios"])

if menu == "Lançamentos":
    st.header("📝 Lançamentos")
    tab1, tab2, tab3 = st.tabs(["Lançar", "Nova Conta", "Gerenciar"])
    with tab2:
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO CIRCULANTE ESTOQUE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV", "ENCARGOS FINANCEIROS"])
        if st.button("Salvar Conta"):
            supabase.table("contas").insert({"user_id": st.session_state.user.id, "nome_conta": nome, "grupo": grupo}).execute()
            st.rerun()
    with tab1:
        contas = get_data("contas")
        lancamentos_full = get_data("lancamentos")
        if contas:
            mapa = {c['nome_conta']: c['id'] for c in contas}
            conta = st.selectbox("Conta", list(mapa.keys()))
            valor = st.number_input("Valor", min_value=0.0)
            op = st.selectbox("Operação", ["DEBITO", "CREDITO"])
            status = st.selectbox("Status", ["ENTRADA", "PAGO", "PENDENTE"])
            data = st.date_input("Data")
            if st.button("Confirmar Lançamento"):
                conta_obj = next(c for c in contas if c['nome_conta'] == conta)
                if conta_obj['grupo'] == 'CMV':
                    df_full = pd.DataFrame(lancamentos_full)
                    st_ids = [c['id'] for c in contas if c['grupo'] == 'ATIVO CIRCULANTE ESTOQUE']
                    st_bal = df_full[df_full['conta_id'].isin(st_ids)].apply(lambda x: x['valor'] if x['operacao']=='DEBITO' else -x['valor'], axis=1).sum()
                    if float(valor) > st_bal:
                        st.error(f"Erro: Valor do CMV excede Estoque (R${st_bal:.2f}).")
                        st.stop()
                supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "conta_id": mapa[conta], "operacao": op, "valor": float(valor), "status_financeiro": status, "data_lancamento": str(data)}).execute()
                st.success("Lançamento efetuado!"); st.rerun()
    with tab3:
        st.write("Gerenciamento de lançamentos...")

elif menu == "Fluxo de Caixa":
    st.header("💵 Fluxo de Caixa")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
        mask_ant = df['data_lancamento'].dt.date < d_inicio
        mask_per = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
        
        saldo_inicial = df[mask_ant].apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else (-x['valor'] if x['status_financeiro'] == 'PAGO' else 0), axis=1).sum()
        df_fc = df[mask_per]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
        col4.metric("Saldo Final", f"R$ {(saldo_inicial + df_fc.apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else (-x['valor'] if x['status_financeiro'] == 'PAGO' else 0), axis=1).sum()):,.2f}")
        st.table(df_fc)

elif menu == "DRE":
    st.header("📈 DRE")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        st.write("Relatório DRE")

elif menu == "Estoque":
    st.header("📦 Estoque")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df_est = df[df['grupo'] == 'ATIVO CIRCULANTE ESTOQUE']
        st.table(df_est)

elif menu == "Contabilidade":
    st.header("📚 Contabilidade")
    tab1, tab2 = st.tabs(["Razonetes", "Balancete"])
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        
        with tab1:
            grupo_sel = st.selectbox("Grupo:", df['grupo'].unique())
            df_g = df[df['grupo'] == grupo_sel]
            cols = st.columns(3)
            for i, conta in enumerate(df_g['nome_conta'].unique()):
                d_c = df_g[df_g['nome_conta'] == conta]
                deb = d_c[d_c['operacao'] == 'DEBITO']['valor'].sum()
                cre = d_c[d_c['operacao'] == 'CREDITO']['valor'].sum()
                st.markdown(f'<div class="t-account"><div class="t-title">{conta}</div><table style="width:100%"><tr><td>D:{deb:,.2f}</td><td>C:{cre:,.2f}</td></tr></table><div class="t-saldo">Saldo:{abs(deb-cre):,.2f}</div></div>', unsafe_allow_html=True)
        with tab2:
            st.write("Balancete...")

elif menu == "Relatórios":
    st.header("📄 Relatórios Consolidados")
    if st.button("Gerar PDF"):
        st.success("Download iniciado")
