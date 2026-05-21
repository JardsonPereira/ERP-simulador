import streamlit as st, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css
st.write("--- DEBUG ---")
user = st.session_state.get('user')
if user:
    st.write(f"Usuário Logado ID: {user.id}")
    # Busca bruta do banco
    try:
        dados = supabase.table("lancamentos").select("*").execute()
        st.write("Dados recebidos do banco:", dados.data)
        if len(dados.data) == 0:
            st.warning("O banco retornou uma lista vazia. O RLS pode estar a bloquear ou não há dados para este user_id.")
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
else:
    st.error("Nenhum usuário logado na sessão.")

check_auth(); inject_css(); supabase = get_supabase()


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
    contas = get_data_cached("contas", st.session_state.user.id)
    lancamentos_full = get_data_cached("lancamentos", st.session_state.user.id)
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
                if not df_full.empty and 'conta_id' in df_full.columns:
                    df_stock = df_full[df_full['conta_id'].isin(stock_ids)]
                    stock_bal = df_stock[df_stock['operacao'] == 'DEBITO']['valor'].sum() - df_stock[df_stock['operacao'] == 'CREDITO']['valor'].sum()
                    if float(valor) > stock_bal:
                        st.error(f"Erro: Valor do CMV excede o estoque disponível (R${stock_bal:.2f}).")
                        st.stop()
            supabase.table("lancamentos").insert({"user_id": st.session_state.user.id, "conta_id": mapa[conta], "operacao": op, "valor": float(valor), "status_financeiro": status, "data_lancamento": str(data), "justificativa": just}).execute()
            st.success("Lançamento efetuado!"); st.rerun()

with tab3:
    st.subheader("Gerenciar Lançamentos")
    lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
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
        opcoes = {f"{pd.to_datetime(l['data_lancamento']).strftime('%Y-%m-%d')} | {mapa_id_nome.get(l['conta_id'])} | {l['operacao']} | R$ {l['valor']:.2f}" : l['id'] for l in lancamentos_filtrados}
        
        if not opcoes: st.info("Nenhum lançamento no período.")
        else:
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
