import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
from fpdf import FPDF

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ContabilApp - Sistema Completo", layout="wide")
EMAIL_ADMIN = "jardsonspereira81@gmail.com"

# --- ESTADOS DO SISTEMA ---
if 'user' not in st.session_state: st.session_state.user = None
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'form_count' not in st.session_state: st.session_state.form_count = 0
if 'menu_opcao' not in st.session_state: st.session_state.menu_opcao = "📊 Razonetes"
if 'tem_perfil' not in st.session_state: st.session_state.tem_perfil = False

try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Erro de conexão. Verifique as Secrets.")
    st.stop()

# --- FUNÇÕES ---
def is_admin():
    return st.session_state.user and hasattr(st.session_state.user, 'email') and st.session_state.user.email == EMAIL_ADMIN

def carregar_dados(u_id, usuario_selecionado="Todos"):
    cols = ['id', 'user_id', 'descricao', 'natureza', 'tipo', 'valor', 'justificativa', 'status', 'data_lancamento']
    try:
        if is_admin() and usuario_selecionado == "Todos":
            res = supabase.table("lancamentos").select("*").execute()
        elif is_admin() and usuario_selecionado != "Todos":
            res = supabase.table("lancamentos").select("*").eq("user_id", usuario_selecionado).execute()
        else:
            res = supabase.table("lancamentos").select("*").eq("user_id", u_id).execute()
        
        if not res.data: return pd.DataFrame(columns=cols)
        
        df = pd.DataFrame(res.data)
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento']).dt.date
        df['valor'] = df['valor'].astype(float)
        return df
    except: return pd.DataFrame(columns=cols)

def agrupar_por_conta(df):
    if df.empty: return []
    linhas = []
    for conta in sorted(df['descricao'].unique()):
        sub = df[df['descricao'] == conta]
        d, c = sub[sub['tipo'] == 'Débito']['valor'].sum(), sub[sub['tipo'] == 'Crédito']['valor'].sum()
        nat = sub['natureza'].iloc[0]
        saldo = (d - c) if ('Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']) else (c - d)
        linhas.append((conta.title(), abs(saldo)))
    return linhas

def total_grupo_com_sinal(df, nat):
    if df.empty: return 0.0
    d, c = df[df['tipo'] == 'Débito']['valor'].sum(), df[df['tipo'] == 'Crédito']['valor'].sum()
    return (d - c) if ('Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']) else (c - d)

# --- AUTENTICAÇÃO E PERFIS ---
if st.session_state.user is None:
    st.sidebar.title("🔐 Login")
    email = st.sidebar.text_input("E-mail").lower().strip()
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        try:
            st.session_state.user = supabase.auth.sign_in_with_password({"email": email, "password": senha}).user
            st.rerun()
        except: st.error("Falha no login.")
    st.stop()

# --- FORÇAR PERFIL ---
if not st.session_state.tem_perfil:
    res = supabase.table("perfis").select("nome_usuario").eq("id", st.session_state.user.id).execute()
    if not res.data:
        st.title("Complete seu Cadastro")
        nome = st.text_input("Nome/Empresa").upper()
        if st.button("Salvar"):
            supabase.table("perfis").insert({"id": st.session_state.user.id, "nome_usuario": nome}).execute()
            st.session_state.tem_perfil = True
            st.rerun()
        st.stop()
    else: st.session_state.tem_perfil = True

# --- SIDEBAR E FILTRO ADMIN ---
with st.sidebar:
    st.write(f"Logado como: {st.session_state.user.email}")
    id_usuario_filtrado = st.session_state.user.id
    if is_admin():
        st.divider()
        perfis = supabase.table("perfis").select("id, nome_usuario").execute().data
        map_user = {p['nome_usuario']: p['id'] for p in perfis}
        map_user = {"Todos": "Todos", "Meu Usuário (Admin)": st.session_state.user.id, **map_user}
        nome_sel = st.selectbox("Filtrar Usuário:", list(map_user.keys()))
        id_usuario_filtrado = map_user[nome_sel]

    if st.button("Sair"):
        st.session_state.user = None
        st.rerun()

# --- CARREGAR DADOS ---
df_base = carregar_dados(st.session_state.user.id, id_usuario_filtrado)
data_ini = st.date_input("Início", datetime.now().replace(day=1))
data_fim = st.date_input("Fim", datetime.now())
df_periodo = df_base[(df_base['data_lancamento'] >= data_ini) & (df_base['data_lancamento'] <= data_fim)].copy()

# --- FORMULÁRIO DE LANÇAMENTO (RESTRITO AO PRÓPRIO USUÁRIO) ---
if id_usuario_filtrado == st.session_state.user.id:
    st.header("➕ Lançamento")
    with st.form("form_lanc"):
        desc = st.text_input("Descrição")
        nat = st.selectbox("Natureza", ["Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido", "Receita", "Despesa", "Encargos Financeiros"])
        tipo = st.radio("Tipo", ["Débito", "Crédito"], horizontal=True)
        valor = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Lançar"):
            supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "descricao": desc, "natureza": nat, "tipo": tipo, "valor": valor, "data_lancamento": str(data_fim)}).execute()
            st.rerun()
else:
    st.warning("Visualizando dados de outro usuário. A inserção está bloqueada.")

# --- CONTEÚDO PRINCIPAL ---
tabs = st.tabs(["Razonetes", "DRE", "Gestão"])
with tabs[0]:
    for nat in df_periodo['natureza'].unique():
        st.subheader(nat)
        st.dataframe(df_periodo[df_periodo['natureza'] == nat])

with tabs[1]:
    v_rec = df_periodo[(df_periodo['natureza'] == 'Receita')]['valor'].sum()
    v_desp = df_periodo[(df_periodo['natureza'] == 'Despesa')]['valor'].sum()
    st.metric("Resultado Operacional", f"R$ {v_rec - v_desp:,.2f}")

with tabs[2]:
    if st.button("🚨 Resetar Meus Dados"):
        supabase.table("lancamentos").delete().eq("user_id", st.session_state.user.id).execute()
        st.rerun()
    st.dataframe(df_base)
