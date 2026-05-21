import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv

# Configuração
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="ERP Didático", layout="wide")

# --- AUTENTICAÇÃO ---
if 'user' not in st.session_state:
    st.title("Login / Cadastro")
    email = st.text_input("Email")
    password = st.text_input("Senha", type="password")
    username = st.text_input("Nome de Usuário")
    
    col1, col2 = st.columns(2)
    if col1.button("Cadastrar"):
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table("profiles").insert({"id": res.user.id, "username": username}).execute()
            st.success("Conta criada! Faça login.")
            
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error("Erro no login.")
    st.stop()

# --- INTERFACE PRINCIPAL ---
st.sidebar.title(f"ERP - {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Estoque", "DRE", "Fluxo de Caixa"])

def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- ABA LANÇAMENTOS ---
if menu == "Lançamentos":
    st.header("Lançamentos Contábeis")
    tab1, tab2 = st.tabs(["Realizar Lançamento", "Nova Conta"])
    
    with tab2:
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV"])
        if st.button("Salvar Conta"):
            supabase.table("contas").insert({"user_id": st.session_state.user.id, "nome_conta": nome, "grupo": grupo}).execute()
            st.success("Conta salva!")
            st.rerun()

    with tab1:
        contas = get_data("contas")
        if not contas:
            st.warning("Crie uma conta primeiro.")
        else:
            mapa = {c['nome_conta']: c['id'] for c in contas}
            c1, c2 = st.columns(2)
            with c1:
                conta = st.selectbox("Conta", list(mapa.keys()))
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            with c2:
                op = st.selectbox("Operação", ["DEBITO", "CREDITO"])
                status = st.selectbox("Status", ["ENTRADA", "PAGO", "PENDENTE", "INVESTIMENTO", "TRANSAÇÃO INTERNA"])
                data = st.date_input("Data do Lançamento")
            
            if st.button("Confirmar Lançamento"):
                supabase.table("lancamentos").insert({
                    "user_id": st.session_state.user.id, "conta_id": mapa[conta],
                    "operacao": op, "valor": valor, "status_financeiro": status, "data_lancamento": str(data)
                }).execute()
                st.success("Lançamento efetuado!")

# --- ABA CONTABILIDADE (RAZONETES/BALANCETE) ---
elif menu == "Contabilidade":
    st.header("Contabilidade: Razonetes e Balancete")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    
    if lancamentos and contas:
        df_l = pd.DataFrame(lancamentos)
        df_c = pd.DataFrame(contas)
        df = df_l.merge(df_c, left_on='conta_id', right_on='id')
        
        # Razonetes
        for nome_conta in df['nome_conta'].unique():
            with st.expander(f"Razonete: {nome_conta}"):
                st.table(df[df['nome_conta'] == nome_conta][['operacao', 'valor', 'data_lancamento']])

        # Balancete
        st.subheader("Balancete de Verificação")
        balancete = df.groupby(['grupo', 'nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
        balancete['Saldo'] = balancete.get('DEBITO', 0) - balancete.get('CREDITO', 0)
        st.table(balancete)
        
        # Verificação de Equilíbrio
        total_d = balancete.get('DEBITO', 0).sum()
        total_c = balancete.get('CREDITO', 0).sum()
        if abs(total_d - total_c) < 0.01:
            st.success(f"Equilibrado! Débitos: R${total_d:.2f} | Créditos: R${total_c:.2f}")
        else:
            st.error(f"Desequilibrado! Débitos: R${total_d:.2f} | Créditos: R${total_c:.2f}")

# --- ESTRUTURA ABAS RESTANTES ---
elif menu in ["Estoque", "DRE", "Fluxo de Caixa"]:
    st.header(f"Módulo: {menu}")
    st.info("Funcionalidade em desenvolvimento. Utilize a base de dados acima para construir os relatórios.")
