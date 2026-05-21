import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ContabilApp - Sistema Integrado", layout="wide")

# --- CONFIGURAÇÃO DE ADMINISTRAÇÃO ---
EMAIL_ADMIN = "jardsonspereira81@gmail.com"

# --- ESTADOS DO SISTEMA ---
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
    st.error("Erro de conexão. Verifique as Secrets no Streamlit Cloud.")
    st.stop()

# --- FUNÇÕES ---
def is_admin():
    if st.session_state.user and hasattr(st.session_state.user, 'email'):
        return st.session_state.user.email == EMAIL_ADMIN
    return False

def verificar_perfil(u_id):
    try:
        res = supabase.table("perfis").select("nome_usuario").eq("id", u_id).execute()
        if res.data:
            st.session_state.tem_perfil = True
            return True
        st.session_state.tem_perfil = False
        return False
    except Exception:
        return False

def obter_todos_usuarios_mapeados():
    mapeamento = {"Todos os Usuários": "Todos"}
    try:
        res_perfis = supabase.table("perfis").select("id, nome_usuario").execute()
        df_perfis = pd.DataFrame(res_perfis.data)
        res_lanc = supabase.table("lancamentos").select("user_id").execute()
        df_lanc = pd.DataFrame(res_lanc.data)
        perfis_dict = {}
        if not df_perfis.empty and 'id' in df_perfis.columns and 'nome_usuario' in df_perfis.columns:
            perfis_dict = dict(zip(df_perfis['id'], df_perfis['nome_usuario']))
        if not df_lanc.empty and 'user_id' in df_lanc.columns:
            ids_unicos = df_lanc['user_id'].unique().tolist()
            for uid in ids_unicos:
                if uid in perfis_dict:
                    mapeamento[perfis_dict[uid]] = uid
                elif uid == st.session_state.user.id:
                    mapeamento[f"Admin ({st.session_state.user.email})"] = uid
                else:
                    mapeamento[f"Sem Nome ({uid[:8]}...)"] = uid
        return mapeamento
    except Exception:
        return {"Todos os Usuários": "Todos"}

def carregar_dados(u_id, usuario_selecionado="Todos"):
    try:
        if is_admin() and usuario_selecionado == "Todos":
            res = supabase.table("lancamentos").select("*").execute()
        elif is_admin() and usuario_selecionado != "Todos":
            res = supabase.table("lancamentos").select("*").eq("user_id", usuario_selecionado).execute()
        else:
            res = supabase.table("lancamentos").select("*").eq("user_id", u_id).execute()
        
        temp_df = pd.DataFrame(res.data)
        if not temp_df.empty:
            temp_df.columns = temp_df.columns.str.strip()
            # Conversão segura
            if 'data_lancamento' in temp_df.columns:
                temp_df['data_lancamento'] = pd.to_datetime(temp_df['data_lancamento']).dt.date
            if 'status' not in temp_df.columns: temp_df['status'] = 'Pago'
            if 'justificativa' not in temp_df.columns: temp_df['justificativa'] = ''
            temp_df['natureza'] = temp_df['natureza'].replace({'Ativo': 'Ativo Circulante', 'Passivo': 'Passivo Circulante'})
        return temp_df
    except Exception: 
        return pd.DataFrame()

def gerar_pdf(user_email, df_per, df_bal, data_i, data_f, s_ini, s_fin, v_at, v_pas, v_pl, v_rec_total, v_desp_total, v_ebitda, v_finan_total, v_lucro):
    pdf = FPDF()
    pdf.add_page()
    def clean_str(s): return str(s).encode('latin-1', 'ignore').decode('latin-1')
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 8, clean_str("RELATÓRIO CONTÁBIL CONSOLIDADO"), ln=True, align="C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(190, 5, clean_str(f"Usuário: {user_email}"), ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 7, clean_str("1. FLUXO DE CAIXA"), ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(63, 7, clean_str(f"Saldo Inicial: R$ {s_ini:,.2f}"), border=1)
    pdf.cell(63, 7, clean_str(f"Saldo Final: R$ {s_fin:,.2f}"), border=1)
    pdf.cell(64, 7, clean_str(f"Variação: R$ {s_fin - s_ini:,.2f}"), border=1, ln=True)
    return pdf.output()

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

# --- AUTENTICAÇÃO ---
if st.session_state.user is None:
    st.sidebar.title("🔐 Acesso")
    menu = st.sidebar.radio("Escolha", ["Login", "Criar Conta"])
    email = st.sidebar.text_input("E-mail").lower().strip()
    senha = st.sidebar.text_input("Senha", type="password")
    if menu == "Login" and st.sidebar.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except: st.sidebar.error("E-mail ou senha incorretos.")
    elif menu == "Criar Conta" and st.sidebar.button("Cadastrar"):
        try:
            supabase.auth.sign_up({"email": email, "password": senha})
            st.sidebar.success("Conta criada! Faça o login agora.")
        except Exception as e: st.sidebar.error(f"Erro: {e}")
    st.stop()

# --- FORÇAR COMPLEMENTO DE CADASTRO ---
if not verificar_perfil(st.session_state.user.id):
    st.title("📋 Complete o seu Cadastro")
    with st.form("form_cadastro"):
        nome_input = st.text_input("Nome Corporativo").upper().strip()
        if st.form_submit_button("Salvar"):
            supabase.table("perfis").insert({"id": st.session_state.user.id, "nome_usuario": nome_input}).execute()
            st.rerun()
    st.stop()

# --- PROCESSAMENTO LATERAL ---
with st.sidebar:
    if st.button("Sair"):
        st.session_state.user = None
        st.rerun()
    if is_admin():
        dict_usuarios = obter_todos_usuarios_mapeados()
        nome_selecionado = st.selectbox("Filtrar lançamentos de:", list(dict_usuarios.keys()))
        id_usuario_filtrado = dict_usuarios[nome_selecionado]

# --- CARREGAMENTO OFICIAL ---
df_base = carregar_dados(st.session_state.user.id, id_usuario_filtrado)

# --- FILTROS CORRIGIDOS ---
f1, f2 = st.columns(2)
with f1: data_ini = st.date_input("Início", value=datetime.now().date().replace(day=1))
with f2: data_fim = st.date_input("Fim", value=datetime.now().date())

# APLICAÇÃO DA CORREÇÃO NO FILTRO
df_base.columns = df_base.columns.str.strip()
if 'data_lancamento' in df_base.columns:
    df_base['data_lancamento'] = pd.to_datetime(df_base['data_lancamento'])
    data_ini_dt = pd.to_datetime(data_ini)
    data_fim_dt = pd.to_datetime(data_fim)
    
    df_periodo = df_base[(df_base['data_lancamento'] >= data_ini_dt) & (df_base['data_lancamento'] <= data_fim_dt)].copy()
    df_balanco = df_base[df_base['data_lancamento'] <= data_fim_dt].copy()
else:
    st.error("Coluna 'data_lancamento' não encontrada no banco. Verifique o Supabase.")
    st.stop()

# --- NAVEGAÇÃO ---
col_nav = st.columns(5)
opcoes_menu = ["📊 Razonetes", "🧾 Balancete", "📈 DRE", "💸 Fluxo de Caixa", "⚙️ Gestão"]
for i, op in enumerate(opcoes_menu):
    if col_nav[i].button(op, use_container_width=True): st.session_state.menu_opcao = op

st.divider()
st.write(f"Conteúdo em: {st.session_state.menu_opcao}")
# [O RESTANTE DO SEU CÓDIGO DE EXIBIÇÃO CONTINUA AQUI...]
