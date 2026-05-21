import streamlit as st
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

st.set_page_config(page_title="ERP Didático", layout="wide")

# --- AUTENTICAÇÃO ---
if 'user' not in st.session_state:
    st.title("Login / Cadastro - ERP Didático")
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
st.sidebar.title(f"ERP: {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Estoque", "DRE", "Fluxo de Caixa"])

# --- ABA LANÇAMENTOS ---
if menu == "Lançamentos":
    st.header("Lançamentos Contábeis")
    tab1, tab2, tab3 = st.tabs(["Realizar Lançamento", "Nova Conta", "Gerenciar Lançamentos"])
    
    with tab2: # Nova Conta
        st.subheader("Cadastrar Conta")
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV"])
        if st.button("Salvar Conta"):
            supabase.table("contas").insert({"user_id": st.session_state.user.id, "nome_conta": nome, "grupo": grupo}).execute()
            st.success("Conta salva!"); st.rerun()

    with tab1: # Realizar Lançamento
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
            if st.button("Confirmar Lançamento"):
                if not just: st.error("Preencha a justificativa.")
                else:
                    supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "conta_id": mapa[conta], "operacao": op, "valor": float(valor), "status_financeiro": status, "data_lancamento": str(data), "justificativa": just}).execute()
                    st.success("Lançamento efetuado!"); st.rerun()

    with tab3: # Gerenciar
        st.subheader("Gerenciar Lançamentos")
        lancamentos = get_data("lancamentos")
        contas = get_data("contas")
        if lancamentos and contas:
            with st.expander("⚠️ Zona de Perigo"):
                if st.button("Resetar/Apagar TODOS os lançamentos", type="primary"):
                    supabase.table("lancamentos").delete().eq("user_id", st.session_state.user.id).execute()
                    st.rerun()
            mapa_id_nome = {c['id']: c['nome_conta'] for c in contas}
            mapa_nome_id = {c['nome_conta']: c['id'] for c in contas}
            opcoes = {f"{l['data_lancamento']} | {mapa_id_nome.get(l['conta_id'])} | {l['operacao']} | R$ {l['valor']:.2f} | {l.get('justificativa', '-')}" : l['id'] for l in lancamentos}
            selecao = st.selectbox("Selecione para Editar/Excluir:", list(opcoes.keys()))
            id_sel = opcoes[selecao]
            item = next(i for i in lancamentos if i["id"] == id_sel)
            with st.form("edit_form"):
                n_conta = st.selectbox("Conta", list(mapa_nome_id.keys()), index=list(mapa_nome_id.values()).index(item['conta_id']))
                n_op = st.selectbox("Operação", ["DEBITO", "CREDITO"], index=["DEBITO", "CREDITO"].index(item['operacao']))
                n_val = st.number_input("Valor", value=float(item['valor']))
                n_just = st.text_input("Justificativa", value=item.get('justificativa', ''))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("Atualizar"):
                    supabase.table("lancamentos").update({"conta_id": int(mapa_nome_id[n_conta]), "operacao": n_op, "valor": float(n_val), "justificativa": n_just}).eq("id", int(id_sel)).execute()
                    st.rerun()
                if c2.form_submit_button("Excluir", type="primary"):
                    supabase.table("lancamentos").delete().eq("id", int(id_sel)).execute()
                    st.rerun()

# --- ABA CONTABILIDADE ---
elif menu == "Contabilidade":
    st.header("Contabilidade")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        
        # Correção Robustez Justificativa
        if 'justificativa' not in df.columns: df = df.assign(justificativa='-')
        df['justificativa'] = df['justificativa'].fillna('-')
        
        # Filtro de Período
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        st.subheader("Filtrar por Período")
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Data Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Data Fim", value=df['data_lancamento'].max().date())
        
        # Aplicação do Filtro
        mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
        df_f = df.loc[mask]
        
        st.divider()
            
        tab_r, tab_b = st.tabs(["Razonetes", "Balancete"])
        with tab_r:
            for grupo in df_f['grupo'].unique():
                st.markdown(f"### 📁 {grupo}")
                df_g = df_f[df_f['grupo'] == grupo]
                cols = st.columns(2)
                for i, nome_conta in enumerate(df_g['nome_conta'].unique()):
                    d_conta = df_g[df_g['nome_conta'] == nome_conta]
                    deb = d_conta[d_conta['operacao'] == 'DEBITO'].reset_index()
                    cre = d_conta[d_conta['operacao'] == 'CREDITO'].reset_index()
                    
                    linhas = ""
                    for j in range(max(len(deb), len(cre))):
                        d_v = f"{deb.loc[j, 'valor']:,.2f}" if j < len(deb) else ""
                        d_j = f"<small style='color:gray'>({deb.loc[j, 'justificativa']})</small>" if j < len(deb) else ""
                        c_v = f"{cre.loc[j, 'valor']:,.2f}" if j < len(cre) else ""
                        c_j = f"<small style='color:gray'>({cre.loc[j, 'justificativa']})</small>" if j < len(cre) else ""
                        linhas += f"<tr><td style='border-right:1px solid #999; text-align:right; font-size:12px;'>{d_v} {d_j}</td><td style='text-align:left; font-size:12px;'>{c_v} {c_j}</td></tr>"
                    
                    html = f"""<div style="border:1px solid #ccc; padding:10px; margin-bottom:20px;">
                    <table style="width:100%"><tr><th colspan="2" style="border-bottom:1px solid #000">{nome_conta}</th></tr>
                    <tr><td style="border-right:1px solid #000; text-align:center">Débito</td><td style="text-align:center">Crédito</td></tr>
                    {linhas}
                    <tr><td style="border-right:1px solid #000; border-top:1px solid #000; text-align:right"><b>{deb['valor'].sum():,.2f}</b></td>
                    <td style="border-top:1px solid #000; text-align:left"><b>{cre['valor'].sum():,.2f}</b></td></tr>
                    </table></div>"""
                    cols[i % 2].markdown(html, unsafe_allow_html=True)
        with tab_b:
            st.table(df_f.groupby(['grupo', 'nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0))
    else:
        st.info("Sem dados.")
