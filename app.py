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
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Fluxo de Caixa", "DRE", "Estoque"])

# --- ABA LANÇAMENTOS ---
if menu == "Lançamentos":
    st.header("Lançamentos Contábeis")
    tab1, tab2, tab3 = st.tabs(["Realizar Lançamento", "Nova Conta", "Gerenciar Lançamentos"])
    
    with tab2:
        st.subheader("Cadastrar Conta")
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO CIRCULANTE ESTOQUE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV", "ENCARGOS FINANCEIROS"])
        if st.button("Salvar Conta"):
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
            if st.button("Confirmar Lançamento"):
                if not just: st.error("Preencha a justificativa.")
                else:
                    supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "conta_id": mapa[conta], "operacao": op, "valor": float(valor), "status_financeiro": status, "data_lancamento": str(data), "justificativa": just}).execute()
                    st.success("Lançamento efetuado!"); st.rerun()

    with tab3:
        st.subheader("Gerenciar Lançamentos")
        lancamentos = get_data("lancamentos")
        contas = get_data("contas")
        if lancamentos and contas:
            df_g = pd.DataFrame(lancamentos)
            df_g['data_lancamento'] = pd.to_datetime(df_g['data_lancamento'])
            c_i, c_f = st.columns(2)
            d_i = c_i.date_input("Data Início (Filtro)", value=df_g['data_lancamento'].min().date())
            d_f = c_f.date_input("Data Fim (Filtro)", value=df_g['data_lancamento'].max().date())
            mask_g = (df_g['data_lancamento'].dt.date >= d_i) & (df_g['data_lancamento'].dt.date <= d_f)
            lancamentos_filtrados = df_g.loc[mask_g].to_dict('records')
            
            with st.expander("⚠️ Zona de Perigo"):
                if st.button("Resetar/Apagar TODOS os lançamentos", type="primary"):
                    supabase.table("lancamentos").delete().eq("user_id", st.session_state.user.id).execute(); st.rerun()
            
            mapa_id_nome = {c['id']: c['nome_conta'] for c in contas}
            mapa_nome_id = {c['nome_conta']: c['id'] for c in contas}
            opcoes = {f"{l['data_lancamento'].date()} | {mapa_id_nome.get(l['conta_id'])} | {l['operacao']} | R$ {l['valor']:.2f}" : l['id'] for l in lancamentos_filtrados}
            if not opcoes: st.info("Nenhum lançamento no período."); st.stop()
            
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
                    supabase.table("lancamentos").update({"conta_id": int(mapa_nome_id[n_conta]), "operacao": n_op, "valor": float(n_val), "justificativa": n_just}).eq("id", int(id_sel)).execute(); st.rerun()
                if c2.form_submit_button("Excluir", type="primary"):
                    supabase.table("lancamentos").delete().eq("id", int(id_sel)).execute(); st.rerun()

# --- ABA DRE ---
elif menu == "DRE":
    st.header("Demonstração do Resultado do Exercício (DRE)")
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
        
        st.subheader("Estrutura da DRE")
        dre_data = {"Descrição": ["(+) Receita Bruta", "(-) CMV", "(=) Lucro Bruto", "(-) Despesas Operacionais", "(-) Encargos Financeiros", "(=) Lucro/Prejuízo Líquido"],
                    "Valor": [receita_bruta, cmv, lucro_bruto, despesas, encargos, lucro_liquido]}
        st.table(pd.DataFrame(dre_data).set_index("Descrição").style.format("R$ {:,.2f}"))
    else: st.info("Dados insuficientes.")

# --- ABA FLUXO DE CAIXA ---
elif menu == "Fluxo de Caixa":
    st.header("Fluxo de Caixa Detalhado")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
        
        mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
        mask_anterior = (df['data_lancamento'].dt.date < d_inicio)
        
        df_fc = df.loc[mask_periodo & df['status_financeiro'].isin(['ENTRADA', 'PAGO'])].copy()
        
        def calcular_fluxo(row):
            if row['status_financeiro'] == 'ENTRADA': return row['valor']
            elif row['status_financeiro'] == 'PAGO': return -row['valor']
            return 0
        df_fc['fluxo'] = df_fc.apply(calcular_fluxo, axis=1)
        
        df_caixa_anterior = df[(df['grupo'] == 'ATIVO CIRCULANTE') & mask_anterior]
        df_caixa_anterior['fluxo'] = df_caixa_anterior.apply(lambda x: x['valor'] if x['operacao'] == 'CREDITO' else -x['valor'], axis=1)
        saldo_inicial = df_caixa_anterior['fluxo'].sum()
        
        entradas = df_fc[df_fc['fluxo'] > 0]['fluxo'].sum()
        saidas = abs(df_fc[df_fc['fluxo'] < 0]['fluxo'].sum())
        saldo_final = (saldo_inicial + entradas - saidas)
        
        st.subheader("Resumo Financeiro")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
        k2.metric("Entradas", f"R$ {entradas:,.2f}")
        k3.metric("Saídas", f"R$ {saidas:,.2f}")
        k4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")
        
        st.table(df_fc[['data_lancamento', 'nome_conta', 'operacao', 'valor', 'status_financeiro']])
        
        st.subheader("Análise de Liquidez e Passivo")
        df_passivo = df[df['grupo'].isin(['PASSIVO CIRCULANTE', 'PASSIVO NÃO CIRCULANTE'])]
        df_passivo['val_contabil'] = df_passivo.apply(lambda x: x['valor'] if x['operacao'] == 'CREDITO' else -x['valor'], axis=1)
        
        passivo_circ = df[df['grupo'] == 'PASSIVO CIRCULANTE']['valor'].sum()
        passivo_total = df_passivo['val_contabil'].sum()
        
        col_res, col_liq = st.columns(2)
        col_res.table(df_passivo.groupby('grupo')['val_contabil'].sum().reset_index())
        col_res.metric("Total Geral Passivo", f"R$ {passivo_total:,.2f}")
        
        liq_circ_perc = (saldo_final / passivo_circ * 100) if passivo_circ > 0 else 0
        liq_total_perc = (saldo_final / passivo_total * 100) if passivo_total > 0 else 0
        
        col_liq.metric("Índice (Saldo Final / Passivo Circ.)", f"{liq_circ_perc:.2f}%")
        col_liq.metric("Índice (Saldo Final / Passivo Total)", f"{liq_total_perc:.2f}%")

    else: st.info("Sem dados.")

# --- ABA ESTOQUE ---
elif menu == "Estoque":
    st.header("Movimentação de Estoque")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        
        # Filtra apenas o grupo de estoque
        df_est = df[df['grupo'] == 'ATIVO CIRCULANTE ESTOQUE'].copy()
        
        # Débito aumenta (entrada), Crédito diminui (saída)
        df_est['tipo'] = df_est.apply(lambda x: "Entrada" if x['operacao'] == 'DEBITO' else "Saída", axis=1)
        df_est['valor_final'] = df_est.apply(lambda x: x['valor'] if x['operacao'] == 'DEBITO' else -x['valor'], axis=1)
        
        total_entradas = df_est[df_est['operacao'] == 'DEBITO']['valor'].sum()
        total_saidas = df_est[df_est['operacao'] == 'CREDITO']['valor'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas (Estoque)", f"R$ {total_entradas:,.2f}")
        c2.metric("Saídas (Estoque)", f"R$ {total_saidas:,.2f}")
        c3.metric("Saldo em Estoque", f"R$ {total_entradas - total_saidas:,.2f}")
        
        st.table(df_est[['data_lancamento', 'nome_conta', 'tipo', 'valor']])
    else: st.info("Nenhuma movimentação de estoque registrada.")

# --- ABA CONTABILIDADE ---
elif menu == "Contabilidade":
    st.header("Contabilidade")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        if 'justificativa' not in df.columns: df = df.assign(justificativa='-')
        df['justificativa'] = df['justificativa'].fillna('-')
        
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
        mask = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
        df_f = df.loc[mask]
            
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
            st.subheader("Balancete de Verificação")
            bal = df_f.groupby(['grupo', 'nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0.0)
            if 'DEBITO' not in bal.columns: bal['DEBITO'] = 0.0
            if 'CREDITO' not in bal.columns: bal['CREDITO'] = 0.0
            bal['SALDO DEVEDOR'] = bal.apply(lambda x: x['DEBITO'] - x['CREDITO'] if x['DEBITO'] > x['CREDITO'] else 0.0, axis=1)
            bal['SALDO CREDOR'] = bal.apply(lambda x: x['CREDITO'] - x['DEBITO'] if x['CREDITO'] > x['DEBITO'] else 0.0, axis=1)
            bal_final = bal.reset_index()
            total_row = pd.DataFrame({
                'grupo': ['TOTAL GERAL'],
                'nome_conta': [''],
                'DEBITO': [bal['DEBITO'].sum()],
                'CREDITO': [bal['CREDITO'].sum()],
                'SALDO DEVEDOR': [bal['SALDO DEVEDOR'].sum()],
                'SALDO CREDOR': [bal['SALDO CREDOR'].sum()]
            })
            bal_final = pd.concat([bal_final, total_row], ignore_index=True)
            st.table(bal_final.style.format({"DEBITO": "R$ {:,.2f}", "CREDITO": "R$ {:,.2f}", "SALDO DEVEDOR": "R$ {:,.2f}", "SALDO CREDOR": "R$ {:,.2f}"}))
    else:
        st.info("Sem dados.")
