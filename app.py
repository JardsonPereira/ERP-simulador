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

# --- FUNÇÃO PDF CONSOLIDADO ---
def gerar_relatorio_pdf(user_name, dre_df, bal_df, fluxo_df, lanc_df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Relatório Contábil Consolidado", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Usuário: {user_name} | Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)

    def add_section(titulo, df):
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, titulo, ln=True)
        pdf.set_font("Arial", size=8)
        header = " | ".join([str(c) for c in df.columns])
        pdf.cell(0, 6, header, border=1, ln=True)
        for _, row in df.iterrows():
            line = " | ".join([str(val) for val in row.values])
            pdf.cell(0, 6, line[:100], border=1, ln=True)
        pdf.ln(5)

    add_section("DRE Detalhada", dre_df)
    add_section("Balanço Patrimonial", bal_df)
    add_section("Fluxo de Caixa", fluxo_df[['data_lancamento', 'nome_conta', 'valor']])
    add_section("Lançamentos", lanc_df[['data_lancamento', 'nome_conta', 'valor', 'operacao']])
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

# --- FUNÇÕES ---
def get_data(table):
    return supabase.table(table).select("*").eq("user_id", st.session_state.user.id).execute().data

# --- NAVEGAÇÃO ---
st.sidebar.title("🏢 ERP Didático")
st.sidebar.caption(f"Usuário: {st.session_state.user.email}")
menu = st.sidebar.radio("Navegação", ["Contabilidade", "Lançamentos", "Fluxo de Caixa", "DRE", "Estoque", "Relatórios"])

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
                conta_selecionada = next(c for c in contas if c['nome_conta'] == conta)
                if conta_selecionada['grupo'] == 'CMV':
                    df_full = pd.DataFrame(lancamentos_full) if lancamentos_full else pd.DataFrame()
                    stock_ids = [c['id'] for c in contas if c['grupo'] == 'ATIVO CIRCULANTE ESTOQUE']
                    if not df_full.empty:
                        df_stock = df_full[df_full['conta_id'].isin(stock_ids)]
                        stock_bal = df_stock[df_stock['operacao'] == 'DEBITO']['valor'].sum() - df_stock[df_stock['operacao'] == 'CREDITO']['valor'].sum()
                        if float(valor) > stock_bal:
                            st.error(f"Erro: Valor do CMV excede o estoque disponível (R${stock_bal:.2f}).")
                            st.stop()
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
            d_i = c_i.date_input("Data Início", value=df_g['data_lancamento'].min().date())
            d_f = c_f.date_input("Data Fim", value=df_g['data_lancamento'].max().date())
            mask_g = (df_g['data_lancamento'].dt.date >= d_i) & (df_g['data_lancamento'].dt.date <= d_f)
            lancamentos_filtrados = df_g.loc[mask_g].to_dict('records')
            
            with st.expander("⚠️ Zona de Perigo"):
                if st.button("Resetar/Apagar TODOS os lançamentos"):
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
    st.header("📈 DRE - Demonstração do Resultado")
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
    else: st.info("Dados insuficientes.")

# --- ABA FLUXO DE CAIXA ---
elif menu == "Fluxo de Caixa":
    st.header("💵 Fluxo de Caixa Detalhado")
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
        
        df_anterior = df[mask_anterior].copy()
        df_anterior['fluxo_ant'] = df_anterior.apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else (-x['valor'] if x['status_financeiro'] == 'PAGO' else 0), axis=1)
        saldo_inicial = df_anterior['fluxo_ant'].sum()
        
        df_fc = df.loc[mask_periodo & df['status_financeiro'].isin(['ENTRADA', 'PAGO'])].copy()
        df_fc['fluxo'] = df_fc.apply(lambda x: x['valor'] if x['status_financeiro'] == 'ENTRADA' else -x['valor'], axis=1)
        
        entradas = df_fc[df_fc['fluxo'] > 0]['fluxo'].sum()
        saidas = abs(df_fc[df_fc['fluxo'] < 0]['fluxo'].sum())
        saldo_final = (saldo_inicial + entradas - saidas)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Saldo Inicial", f"R$ {saldo_inicial:,.2f}")
        col2.metric("Entradas", f"R$ {entradas:,.2f}")
        col3.metric("Saídas", f"R$ {saidas:,.2f}")
        col4.metric("Saldo Final", f"R$ {saldo_final:,.2f}")
        
        st.table(df_fc[['data_lancamento', 'nome_conta', 'operacao', 'valor', 'status_financeiro']])
        
        st.subheader("📊 Análise de Liquidez e Passivo")
        df_passivo = df[df['grupo'].isin(['PASSIVO CIRCULANTE', 'PASSIVO NÃO CIRCULANTE'])]
        df_passivo['val_contabil'] = df_passivo.apply(lambda x: x['valor'] if x['operacao'] == 'CREDITO' else -x['valor'], axis=1)
        
        passivo_circ = df[df['grupo'] == 'PASSIVO CIRCULANTE']['valor'].sum()
        passivo_total = df_passivo['val_contabil'].sum()
        
        c1, c2 = st.columns(2)
        with c1:
            st.table(df_passivo.groupby('grupo')['val_contabil'].sum().reset_index())
            st.metric("Total Geral Passivo", f"R$ {passivo_total:,.2f}")
        
        with c2:
            liq_circ_perc = (saldo_final / passivo_circ * 100) if passivo_circ > 0 else 0
            liq_total_perc = (saldo_final / passivo_total * 100) if passivo_total > 0 else 0
            st.metric("Liquidez (Saldo / Passivo Circ.)", f"{liq_circ_perc:.2f}%")
            st.metric("Liquidez (Saldo / Passivo Total)", f"{liq_total_perc:.2f}%")
    else: st.info("Sem dados.")

# --- ABA ESTOQUE ---
elif menu == "Estoque":
    st.header("📦 Movimentação de Estoque")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df_est = df[df['grupo'] == 'ATIVO CIRCULANTE ESTOQUE'].copy()
        df_est['tipo'] = df_est.apply(lambda x: "Entrada" if x['operacao'] == 'DEBITO' else "Saída", axis=1)
        
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
    st.header("📚 Contabilidade")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        c1, c2 = st.columns(2)
        d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
        d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
        mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
            
        tab_r, tab_b = st.tabs(["Razonetes", "Balancete"])
        with tab_r:
            grupos_disponiveis = df['grupo'].unique()
            grupo_selecionado = st.selectbox("Selecione o Grupo:", grupos_disponiveis)
            df_g = df[df['grupo'] == grupo_selecionado]
            cols = st.columns(3)
            for i, nome_conta in enumerate(df_g['nome_conta'].unique()):
                d_conta = df_g[df_g['nome_conta'] == nome_conta]
                ant = d_conta[d_conta['data_lancamento'].dt.date < d_inicio]
                per = d_conta[mask_periodo]
                deb = per[per['operacao'] == 'DEBITO']['valor'].sum()
                cre = per[per['operacao'] == 'CREDITO']['valor'].sum()
                saldo_ini = ant[ant['operacao'] == 'DEBITO']['valor'].sum() - ant[ant['operacao'] == 'CREDITO']['valor'].sum()
                saldo_fin = abs(saldo_ini + deb - cre)
                st.markdown(f"""
                <div class="t-account">
                    <div class="t-title">{nome_conta} (Ini: {saldo_ini:,.2f})</div>
                    <table style="width:100%">
                        <tr><td style="text-align:center; border-right:1px solid #ddd">Débito</td><td style="text-align:center">Crédito</td></tr>
                        <tr><td style="text-align:center; color: #28a745;"><b>{deb:,.2f}</b></td><td style="text-align:center; color: #dc3545;"><b>{cre:,.2f}</b></td></tr>
                    </table>
                    <div class="t-saldo">Saldo Final: {saldo_fin:,.2f}</div>
                </div>""", unsafe_allow_html=True)
        with tab_b:
            bal = df[mask_periodo].groupby(['grupo', 'nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0.0)
            st.table(bal)
    else: st.info("Sem dados.")

# --- ABA RELATÓRIOS (PDF CONSOLIDADO) ---
elif menu == "Relatórios":
    st.header("📄 Relatórios Consolidados")
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    if lancamentos and contas:
        df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
        
        # Filtragem por período
        c1, c2 = st.columns(2)
        d_i = c1.date_input("Período Início", value=df['data_lancamento'].min().date())
        d_f = c2.date_input("Período Fim", value=df['data_lancamento'].max().date())
        mask = (df['data_lancamento'].dt.date >= d_i) & (df['data_lancamento'].dt.date <= d_f)
        df_p = df.loc[mask]
        
        # DRE e Balanço simplificados para relatório
        dre = df_p[df_p['grupo'].isin(['RECEITAS', 'DESPESAS', 'CMV'])].groupby('grupo')['valor'].sum().reset_index()
        bal = df_p.groupby(['grupo', 'nome_conta'])['valor'].sum().reset_index()
        
        if st.download_button("Baixar PDF Consolidado", data=gerar_relatorio_pdf(st.session_state.user.email, dre, bal, df_p, df_p), file_name="relatorio.pdf"):
            st.success("Download iniciado!")
    else: st.info("Dados insuficientes.")
