import streamlit as st
import pandas as pd
from supabase import create_client

# Configuração e Conexão
st.set_page_config(layout="wide")
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

if 'user' not in st.session_state: st.session_state.user = None

# --- LÓGICA DO SISTEMA ---
def registrar_lancamento(user_id, desc, nat, tipo, valor, justificativa, status, data):
    payload = {
        "user_id": user_id, "descricao": desc, "natureza": nat, "tipo": tipo,
        "valor": valor, "justificativa": justificativa, "status": status,
        "data_lancamento": str(data)
    }
    supabase.table("lancamentos").insert(payload).execute()

# --- TELAS ---
def mostrar_sistema(user_id, email):
    # Carrega lançamentos do banco
    lanc = supabase.table("lancamentos").select("*").execute().data
    df = pd.DataFrame(lanc) if lanc else pd.DataFrame()
    if not df.empty: df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])

    menu = st.sidebar.radio("Navegação", ["🛒 Lançamentos", "📊 Razonetes", "🧾 Balancete", "📈 DRE"])

    if menu == "🛒 Lançamentos":
        st.header("Entradas e Saídas")
        col1, col2 = st.columns(2)
        with col1:
            with st.form("entrada"):
                st.subheader("📥 Entrada")
                desc = st.text_input("Descrição")
                nat = st.selectbox("Grupo", ["Ativo", "Receitas", "Investimentos"])
                tipo = st.radio("Operação", ["Débito", "Crédito"])
                valor = st.number_input("Valor", min_value=0.0)
                status = st.selectbox("Status", ["Entrada", "Pendente", "Investimento"])
                if st.form_submit_button("Confirmar Entrada"):
                    registrar_lancamento(user_id, desc, nat, tipo, valor, "Entrada", status, pd.Timestamp.now())
                    st.rerun()
        with col2:
            with st.form("saida"):
                st.subheader("📤 Saída")
                desc = st.text_input("Descrição", key="s_desc")
                nat = st.selectbox("Grupo", ["Passivo", "CMV", "Despesas", "Encargos"])
                tipo = st.radio("Operação", ["Débito", "Crédito"], key="s_tipo")
                valor = st.number_input("Valor", min_value=0.0, key="s_valor")
                status = st.selectbox("Status", ["Pago", "Pendente"], key="s_status")
                if st.form_submit_button("Confirmar Saída"):
                    registrar_lancamento(user_id, desc, nat, tipo, valor, "Saída", status, pd.Timestamp.now())
                    st.rerun()

    elif menu == "📊 Razonetes":
        st.header("📊 Razonetes (Partidas Dobradas)")
        for natureza, grupo in df.groupby('natureza'):
            st.write(f"### Conta: {natureza}")
            c1, c2 = st.columns(2)
            c1.table(grupo[grupo['tipo'] == 'Débito'][['descricao', 'valor']])
            c2.table(grupo[grupo['tipo'] == 'Crédito'][['descricao', 'valor']])

    elif menu == "🧾 Balancete":
        st.header("🧾 Balancete")
        st.table(df.groupby(['natureza', 'tipo'])['valor'].sum().unstack(fill_value=0))

    elif menu == "📈 DRE":
        st.header("📈 DRE")
        receitas = df[df['natureza'] == 'Receitas']['valor'].sum()
        despesas = df[df['natureza'].isin(['CMV', 'Despesas'])]['valor'].sum()
        st.metric("Lucro Líquido", f"R$ {receitas - despesas:,.2f}")

# --- LOGIN ---
if not st.session_state.user:
    email = st.sidebar.text_input("E-mail")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except: st.error("Erro de Login")
else:
    mostrar_sistema(st.session_state.user.id, st.session_state.user.email)
