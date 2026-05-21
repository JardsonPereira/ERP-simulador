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

# --- FUNÇÃO DE RELATÓRIO CONSOLIDADO ---
def gerar_relatorio_consolidado(usuario, periodo, saldo_ini, saldo_fin, df_dre, df_balanco):
    pdf = FPDF()
    pdf.add_page()
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
    pdf.cell(0, 8, f"Saldo Inicial: R$ {float(saldo_ini):,.2f}", ln=True)
    pdf.cell(0, 8, f"Saldo Final: R$ {float(saldo_fin):,.2f}", ln=True)
    pdf.ln(10)
    
    # 2. DRE
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DEMONSTRAÇÃO DO RESULTADO (DRE)", ln=True)
    pdf.set_font("Arial", size=10)
    for _, row in df_dre.iterrows():
        pdf.cell(0, 8, f"{row.iloc[0]}: R$ {float(row.iloc[1]):,.2f}", ln=True)
    pdf.ln(10)
    
    # 3. Balanço
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. BALANÇO PATRIMONIAL CONSOLIDADO", ln=True)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 10, "Conta", border=1); pdf.cell(95, 10, "Valor (R$)", border=1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for _, row in df_balanco.iterrows():
        pdf.cell(95, 8, str(row.iloc[0]), border=1)
        pdf.cell(95, 8, f"{float(row.iloc[1]):,.2f}", border=1)
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

# --- SIDEBAR: RELATÓRIO CONSOLIDADO ---
if st.sidebar.button("📄 Baixar Relatório Completo"):
    lanc = get_data("lancamentos")
    cont = get_data("contas")
    if lanc and cont:
        df = pd.DataFrame(lanc).merge(pd.DataFrame(cont), left_on='conta_id', right_on='id')
        dre_ex = pd.DataFrame({"Desc": ["Receita", "Lucro"], "Val": [0, 0]})
        bal_ex = pd.DataFrame({"Conta": ["Caixa"], "Val": [0]})
        pdf_data = gerar_relatorio_consolidado(st.session_state.user.email, "Geral", 0, 0, dre_ex, bal_ex)
        st.download_button("Clique aqui para baixar", data=pdf_data, file_name="relatorio_final.pdf")

# --- ABA LANÇAMENTOS ---
if menu == "Lançamentos":
    st.header("📝 Lançamentos Contábeis")
    tab1, tab2, tab3 = st.tabs(["Realizar Lançamento", "Nova Conta", "Gerenciar Lançamentos"])
    with tab2:
        st.subheader("Cadastrar Nova Conta")
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO CIRCULANTE ESTOQUE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV", "ENCARGOS FINANCEIROS"])
        if st.button("Salvar Conta", type="primary"):
            supabase.table("contas").insert({"user_id": st.session_state.user.id, "nome_conta": nome, "grupo": grupo}).execute()
            st.success("Conta salva!"); st.rerun()
    with tab1:
        contas = get_data("contas")
        if not contas: st.warning("Crie uma conta primeiro.")
        else:
            mapa = {c['nome_conta']: c['id'] for c in contas}
            c1, c2 = st.columns(2)
            conta = c1.selectbox("Conta", list(mapa.keys()))
            valor = c1.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            just = c1.text_input("Justificativa")
            op = c2.selectbox("Operação", ["DEBITO", "CREDITO"])
            status = c2.selectbox("Status", ["ENTRADA", "PAGO", "PENDENTE", "INVESTIMENTO", "TRANSAÇÃO INTERNA"])
            data = c2.date_input("Data do Lançamento")
            if st.button("Confirmar Lançamento", type="primary"):
                supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "conta_id": mapa[conta], "operacao": op, "valor": float(valor), "status_financeiro": status, "data_lancamento": str(data), "justificativa": just}).execute()
                st.success("Lançamento efetuado!"); st.rerun()
    with tab3:
        st.subheader("Gerenciar Lançamentos")
        lancamentos = get_data("lancamentos")
        contas = get_data("contas")
        if lancamentos and contas:
            df_g = pd.DataFrame(lancamentos)
            df_g['data_lancamento'] = pd.to_datetime(df_g['data_lancamento'])
            mapa_id_nome = {c['id']: c['nome_conta'] for c in contas}
            opcoes = {f"{l['data_lancamento'].strftime('%Y-%m-%d')} | {mapa_id_nome.get(l['conta_id'])} | {l['operacao']} | R$ {l['valor']:.2f}" : l['id'] for l in lancamentos}
            selecao = st.selectbox("Selecione para Excluir:", list(opcoes.keys()))
            if st.button("Excluir"):
                supabase.table("lancamentos").delete().eq("id", opcoes[selecao]).execute(); st.rerun()

# --- ABA DRE ---
elif menu == "DRE":
    st.header("📈 DRE")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        receita = df[df['grupo'] == 'RECEITAS']['valor'].sum()
        cmv = df[df['grupo'] == 'CMV']['valor'].sum()
        desp = df[df['grupo'] == 'DESPESAS']['valor'].sum()
        lucro = receita - cmv - desp
        dre_data = pd.DataFrame({"Descrição": ["(+) Receita", "(-) CMV", "(-) Despesas", "(=) Lucro"], "Valor": [receita, cmv, desp, lucro]})
        st.table(dre_data)

# --- ABA FLUXO DE CAIXA ---
elif menu == "Fluxo de Caixa":
    st.header("💵 Fluxo de Caixa")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        st.table(df[['data_lancamento', 'nome_conta', 'valor']])

# --- ABA ESTOQUE ---
elif menu == "Estoque":
    st.header("📦 Estoque")
    st.info("Movimentação de estoque.")

# --- ABA CONTABILIDADE ---
elif menu == "Contabilidade":
    st.header("📚 Contabilidade")
    st.write("Razonetes e Balancete.")
