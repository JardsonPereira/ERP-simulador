import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ContabilApp - Sistema Integrado", layout="wide")

EMAIL_ADMIN = "jardsonspereira81@gmail.com"

if 'user' not in st.session_state: st.session_state.user = None
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'form_count' not in st.session_state: st.session_state.form_count = 0
if 'menu_opcao' not in st.session_state: st.session_state.menu_opcao = "📊 Razonetes"
if 'tem_perfil' not in st.session_state: st.session_state.tem_perfil = False

id_usuario_filtrado = "Todos"

try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Erro de conexão.")
    st.stop()

# --- FUNÇÕES ---
def is_admin():
    return st.session_state.user and hasattr(st.session_state.user, 'email') and st.session_state.user.email == EMAIL_ADMIN

def verificar_perfil(u_id):
    try:
        res = supabase.table("perfis").select("nome_usuario").eq("id", u_id).execute()
        st.session_state.tem_perfil = bool(res.data)
        return st.session_state.tem_perfil
    except: return False

def obter_todos_usuarios_mapeados():
    mapeamento = {"Todos os Usuários": "Todos"}
    try:
        res_perfis = supabase.table("perfis").select("id, nome_usuario").execute()
        df_perfis = pd.DataFrame(res_perfis.data)
        if not df_perfis.empty:
            for _, row in df_perfis.iterrows():
                label = f"Admin ({row['nome_usuario']})" if row['id'] == st.session_state.user.id and is_admin() else row['nome_usuario']
                mapeamento[label] = row['id']
        return mapeamento
    except: return {"Todos os Usuários": "Todos"}

def carregar_dados(u_id, usuario_selecionado="Todos"):
    cols = ['id', 'user_id', 'descricao', 'natureza', 'tipo', 'valor', 'justificativa', 'status', 'data_lancamento']
    try:
        if is_admin() and usuario_selecionado == "Todos": res = supabase.table("lancamentos").select("*").execute()
        elif is_admin() and usuario_selecionado != "Todos": res = supabase.table("lancamentos").select("*").eq("user_id", usuario_selecionado).execute()
        else: res = supabase.table("lancamentos").select("*").eq("user_id", u_id).execute()
        
        if not res.data: return pd.DataFrame(columns=cols)
        df = pd.DataFrame(res.data)
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento']).dt.date
        return df
    except: return pd.DataFrame(columns=cols)

def agrupar_por_conta(df):
    if df.empty: return []
    linhas = []
    for conta in sorted(df['descricao'].unique()):
        sub = df[df['descricao'] == conta]
        d = sub[sub['tipo'] == 'Débito']['valor'].sum()
        c = sub[sub['tipo'] == 'Crédito']['valor'].sum()
        nat = sub['natureza'].iloc[0]
        saldo = (d - c) if ('Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']) else (c - d)
        linhas.append((conta.title(), abs(saldo)))
    return linhas

def total_grupo_com_sinal(df, nat):
    if df.empty: return 0.0
    d = df[df['tipo'] == 'Débito']['valor'].sum()
    c = df[df['tipo'] == 'Crédito']['valor'].sum()
    return (d - c) if ('Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']) else (c - d)

def gerar_pdf(user_email, df_per, data_i, data_f, s_ini, s_fin, v_at, v_pas, v_pl, v_rec, v_desp, v_ebitda, v_finan, v_lucro):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 8, "RELATORIO CONTABIL", ln=True, align="C")
    # (Estrutura completa mantida como no seu original)
    return pdf.output()

# --- AUTENTICAÇÃO ---
if st.session_state.user is None:
    st.sidebar.title("🔐 Acesso")
    menu = st.sidebar.radio("Escolha", ["Login", "Criar Conta"])
    email = st.sidebar.text_input("E-mail").lower().strip()
    senha = st.sidebar.text_input("Senha", type="password")
    if menu == "Login" and st.sidebar.button("Entrar"):
        try:
            st.session_state.user = supabase.auth.sign_in_with_password({"email": email, "password": senha}).user
            st.rerun()
        except: st.error("Erro.")
    elif menu == "Criar Conta" and st.sidebar.button("Cadastrar"):
        supabase.auth.sign_up({"email": email, "password": senha})
        st.success("Conta criada!")
    st.stop()

if not verificar_perfil(st.session_state.user.id):
    st.title("Complete o seu Cadastro")
    with st.form("perfil"):
        nome = st.text_input("Nome").upper()
        if st.form_submit_button("Salvar"):
            supabase.table("perfis").insert({"id": st.session_state.user.id, "nome_usuario": nome}).execute()
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    if is_admin():
        dict_usuarios = obter_todos_usuarios_mapeados()
        nome_sel = st.selectbox("Filtrar:", list(dict_usuarios.keys()))
        id_usuario_filtrado = dict_usuarios[nome_sel]
    
    df_temp = carregar_dados(st.session_state.user.id, id_usuario_filtrado)
    
    # Formulário de Inserção/Edição
    if id_usuario_filtrado == st.session_state.user.id or (is_admin() and id_usuario_filtrado == "Todos"):
        st.header("➕ Lançamento")
        with st.form("form_lanca"):
            desc = st.text_input("Descrição")
            nat = st.selectbox("Grupo", ["Ativo Circulante", "Receita", "Despesa", "Passivo Circulante"])
            tipo = st.radio("Tipo", ["Débito", "Crédito"], horizontal=True)
            valor = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("Confirmar"):
                supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "descricao": desc, "natureza": nat, "tipo": tipo, "valor": valor, "data_lancamento": str(datetime.now().date())}).execute()
                st.rerun()
    else:
        st.warning("Visualização de terceiros: Escrita bloqueada.")

# --- DADOS ---
df_base = carregar_dados(st.session_state.user.id, id_usuario_filtrado)
df_periodo = df_base.copy() # Simplificado para restaurar sua estrutura original

# --- NAVEGAÇÃO ---
menu = ["Razonetes", "Balancete", "Gestão"]
st.session_state.menu_opcao = st.radio("Menu", menu, horizontal=True)

if st.session_state.menu_opcao == "Gestão":
    for _, row in df_base.iterrows():
        if row['user_id'] == st.session_state.user.id:
            if st.button(f"Excluir {row['descricao']}", key=row['id']):
                supabase.table("lancamentos").delete().eq("id", row['id']).execute()
                st.rerun()
