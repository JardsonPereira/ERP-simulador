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

# --- FUNÇÃO DE PDF (ISOLADA) ---
def gerar_pdf(titulo, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo, ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.ln(10)
    for index, row in df.iterrows():
        line = " | ".join([str(val) for val in row.values])
        pdf.cell(0, 10, line, ln=True)
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

# --- ABA LANÇAMENTOS ---
if menu == "Lançamentos":
    st.header("📝 Lançamentos Contábeis")
    tab1, tab2, tab3 = st.tabs(["Realizar Lançamento", "Nova Conta", "Gerenciar Lançamentos"])
    with tab2:
        with st.container():
            st.subheader("Cadastrar Nova Conta")
            nome = st.text_input("Nome da Conta")
            grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO CIRCULANTE ESTOQUE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV", "ENCARGOS FINANCEIROS"])
            if st.button("Salvar Conta", type="primary"):
                supabase.table("contas").insert({"user_id": st.session_state.user.id, "nome_conta": nome, "grupo": grupo}).execute()
                st.success("Conta salva!"); st.rerun()
    with tab1:
        contas = get_data("contas")
        lancamentos_full = get_data("lancamentos")
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
            opcoes = {f"{l['data_lancamento'].date()} | {mapa_id_nome.get(l['conta_id'])} | {l['operacao']} | R$ {l['valor']:.2f}" : l['id'] for l in lancamentos}
            selecao = st.selectbox("Selecione para Editar/Excluir:", list(opcoes.keys()))
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
        c1, c2 = st.columns(2)
        d_i = c1.date_input("Início", value=df['data_lancamento'].min().date())
        d_f = c2.date_input("Fim", value=df['data_lancamento'].max().date())
        mask = (df['data_lancamento'].dt.date >= d_i) & (df['data_lancamento'].dt.date <= d_f)
        df_dre = df.loc[mask]
        
        grupos_dre = ['RECEITAS', 'DESPESAS', 'CMV', 'ENCARGOS FINANCEIROS']
        df_dre = df_dre[df_dre['grupo'].isin(grupos_dre)]
        
        receita_bruta = df_dre[df_dre['grupo'] == 'RECEITAS']['valor'].sum()
        cmv = df_dre[df_dre['grupo'] == 'CMV']['valor'].sum()
        despesas = df_dre[df_dre['grupo'] == 'DESPESAS']['valor'].sum()
        encargos = df_dre[df_dre['grupo'] == 'ENCARGOS FINANCEIROS']['valor'].sum()
        lucro_bruto = receita_bruta - cmv
        lucro_liquido = lucro_bruto - despesas - encargos
        
        dre_data = pd.DataFrame({"Descrição": ["(+) Receita Bruta", "(-) CMV", "(=) Lucro Bruto", "(-) Despesas Operacionais", "(-) Encargos Financeiros", "(=) Lucro/Prejuízo Líquido"],
                                "Valor": [receita_bruta, cmv, lucro_bruto, despesas, encargos, lucro_liquido]})
        st.table(dre_data.set_index("Descrição").style.format("R$ {:,.2f}"))
        
        # Botão mantido ao final sem quebrar a lógica
        if st.download_button("Baixar DRE PDF", data=gerar_pdf("DRE", dre_data), file_name="dre.pdf"): st.success("Download iniciado!")
    else: st.info("Dados insuficientes.")

# --- ABA FLUXO DE CAIXA ---
elif menu == "Fluxo de Caixa":
    st.header("💵 Fluxo de Caixa Detalhado")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        st.table(df[['data_lancamento', 'nome_conta', 'valor']])
        if st.download_button("Baixar Fluxo de Caixa PDF", data=gerar_pdf("Fluxo de Caixa", df), file_name="fluxo.pdf"): st.success("Download iniciado!")
    else: st.info("Sem dados.")

# --- ABA ESTOQUE ---
elif menu == "Estoque":
    st.header("📦 Movimentação de Estoque")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        st.table(df[['data_lancamento', 'nome_conta', 'valor']])

# --- ABA CONTABILIDADE ---
elif menu == "Contabilidade":
    st.header("📚 Contabilidade")
    st.write("Razonetes e Balancete.")
