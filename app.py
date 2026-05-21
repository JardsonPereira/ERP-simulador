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
            except Exception as e:
                st.error(f"Erro ao salvar perfil: {e}")
            
    if col2.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = res.user
            st.rerun()
        except Exception as e:
            st.error(f"Falha no login: {e}")
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
    
    # ----------------------------------------
    # TAB 2: NOVA CONTA
    # ----------------------------------------
    with tab2:
        st.subheader("Cadastrar Conta")
        nome = st.text_input("Nome da Conta")
        grupo = st.selectbox("Grupo", ["ATIVO CIRCULANTE", "ATIVO NÃO CIRCULANTE", "PASSIVO CIRCULANTE", "PASSIVO NÃO CIRCULANTE", "PL", "RECEITAS", "DESPESAS", "CMV"])
        if st.button("Salvar Conta"):
            supabase.table("contas").insert({
                "user_id": st.session_state.user.id, 
                "nome_conta": nome, 
                "grupo": grupo
            }).execute()
            st.success("Conta salva!")
            st.rerun()

    # ----------------------------------------
    # TAB 1: REALIZAR LANÇAMENTO
    # ----------------------------------------
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
                justificativa = st.text_input("Justificativa / Histórico", placeholder="Ex: Pagamento de fornecedor")
                
            with c2:
                op = st.selectbox("Operação", ["DEBITO", "CREDITO"])
                status = st.selectbox("Status", ["ENTRADA", "PAGO", "PENDENTE", "INVESTIMENTO", "TRANSAÇÃO INTERNA"])
                data = st.date_input("Data do Lançamento")
            
            if st.button("Confirmar Lançamento"):
                if not justificativa:
                    st.error("Por favor, preencha a justificativa.")
                else:
                    supabase.table("lancamentos").insert({
                        "user_id": st.session_state.user.id, 
                        "conta_id": mapa[conta],
                        "operacao": op, 
                        "valor": valor, 
                        "status_financeiro": status, 
                        "data_lancamento": str(data),
                        "justificativa": justificativa
                    }).execute()
                    st.success("Lançamento efetuado com sucesso!")
                    st.rerun()

    # ----------------------------------------
    # TAB 3: GERENCIAR (EDITAR, EXCLUIR, RESETAR)
    # ----------------------------------------
    with tab3:
        st.subheader("Gerenciar Lançamentos")
        lancamentos = get_data("lancamentos")
        contas = get_data("contas")
        
        if lancamentos and contas:
            # Prepara dados para exibição
            df_l = pd.DataFrame(lancamentos)
            df_c = pd.DataFrame(contas)
            df_view = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
            
            # Opção de resetar tudo
            st.divider()
            col_reset1, col_reset2 = st.columns([3, 1])
            col_reset1.warning("⚠️ **Zona de Perigo:** Apagar todos os lançamentos é uma ação irreversível.")
            if col_reset2.button("Resetar Todos os Lançamentos", type="primary"):
                supabase.table("lancamentos").delete().eq("user_id", st.session_state.user.id).execute()
                st.success("Todos os lançamentos foram apagados!")
                st.rerun()
            st.divider()

            # Selecionar lançamento para editar/excluir
            opcoes_lancamentos = {f"{row['data_lancamento']} | {row['nome_conta']} | {row['operacao']} | R$ {row['valor']:.2f} | {row.get('justificativa', '-')}": row['id_lanc'] for index, row in df_view.iterrows()}
            
            lancamento_selecionado = st.selectbox("Selecione um lançamento para Editar/Excluir:", list(opcoes_lancamentos.keys()))
            id_selecionado = opcoes_lancamentos[lancamento_selecionado]
            
            # Recupera os dados do lançamento selecionado
            lancamento_atual = next(item for item in lancamentos if item["id"] == id_selecionado)
            
            with st.form("form_editar_lancamento"):
                st.write("**Editar Lançamento Selecionado**")
                mapa_inverso = {c['id']: c['nome_conta'] for c in contas}
                mapa_contas = {c['nome_conta']: c['id'] for c in contas}
                
                # Campos preenchidos com os dados atuais
                nova_conta_nome = st.selectbox("Conta", list(mapa_contas.keys()), index=list(mapa_contas.values()).index(lancamento_atual['conta_id']))
                nova_operacao = st.selectbox("Operação", ["DEBITO", "CREDITO"], index=["DEBITO", "CREDITO"].index(lancamento_atual['operacao']))
                novo_valor = st.number_input("Valor (R$)", min_value=0.0, value=float(lancamento_atual['valor']), format="%.2f")
                nova_justificativa = st.text_input("Justificativa", value=lancamento_atual.get('justificativa', ''))
                
                col_btn1, col_btn2 = st.columns(2)
                btn_salvar = col_btn1.form_submit_button("Atualizar Lançamento")
                btn_excluir = col_btn2.form_submit_button("Excluir Lançamento")
                
                if btn_salvar:
                    supabase.table("lancamentos").update({
                        "conta_id": mapa_contas[nova_conta_nome],
                        "operacao": nova_operacao,
                        "valor": novo_valor,
                        "justificativa": nova_justificativa
                    }).eq("id", id_selecionado).execute()
                    st.success("Lançamento atualizado!")
                    st.rerun()
                    
                if btn_excluir:
                    supabase.table("lancamentos").delete().eq("id", id_selecionado).execute()
                    st.success("Lançamento excluído!")
                    st.rerun()
        else:
            st.info("Nenhum lançamento encontrado para gerenciar.")

# --- ABA CONTABILIDADE (RAZONETES E BALANCETE) ---
elif menu == "Contabilidade":
    st.header("Contabilidade")
    
    lancamentos = get_data("lancamentos")
    contas = get_data("contas")
    
    if lancamentos and contas:
        df_l = pd.DataFrame(lancamentos)
        df_c = pd.DataFrame(contas)
        df = df_l.merge(df_c, left_on='conta_id', right_on='id')
        
        if 'justificativa' not in df.columns:
            df['justificativa'] = "-"
        else:
            df['justificativa'] = df['justificativa'].fillna("-")
            
        btn_razonetes, btn_balancete = st.tabs(["Ver Razonetes (Gráfico T)", "Ver Balancete de Verificação"])
        
        # ----------------------------------------
        # VISUALIZAÇÃO DOS RAZONETES EM FORMATO 'T'
        # ----------------------------------------
        with btn_razonetes:
            st.subheader("Razonetes (Contas em 'T')")
            
            # Criamos colunas para mostrar 2 razonetes por linha (fica mais limpo)
            cols = st.columns(2)
            col_idx = 0
            
            for nome_conta in df['nome_conta'].unique():
                dados_conta = df[df['nome_conta'] == nome_conta]
                
                # Separar débitos e créditos
                debitos = dados_conta[dados_conta['operacao'] == 'DEBITO'].reset_index(drop=True)
                creditos = dados_conta[dados_conta['operacao'] == 'CREDITO'].reset_index(drop=True)
                
                total_debito = debitos['valor'].sum()
                total_credito = creditos['valor'].sum()
                saldo = total_debito - total_credito
                tipo_saldo = "Devedor" if saldo > 0 else "Credor" if saldo < 0 else "Nulo"
                
                # Gerar as linhas dinamicamente (alinhando lado a lado na tabela HTML)
                max_linhas = max(len(debitos), len(creditos))
                linhas_html = ""
                
                for i in range(max_linhas):
                    # Formatar Débito (Justificativa no inicio, valor depois)
                    if i < len(debitos):
                        val_d = f"{debitos.loc[i, 'valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        just_d = debitos.loc[i, 'justificativa']
                        texto_d = f"<span style='color:gray; font-size:12px;'>({just_d})</span> {val_d}"
                    else:
                        texto_d = ""
                        
                    # Formatar Crédito (Valor no inicio, justificativa depois)
                    if i < len(creditos):
                        val_c = f"{creditos.loc[i, 'valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        just_c = creditos.loc[i, 'justificativa']
                        texto_c = f"{val_c} <span style='color:gray; font-size:12px;'>({just_c})</span>"
                    else:
                        texto_c = ""
                        
                    linhas_html += f"""
                    <tr>
                        <td style='width: 50%; border-right: 2px solid #555; padding: 4px; text-align: right;'>{texto_d}</td>
                        <td style='width: 50%; padding: 4px; text-align: left;'>{texto_c}</td>
                    </tr>
                    """

                # Estrutura HTML final do Razonete
                razonete_html = f"""
                <div style="display: flex; justify-content: center; margin-bottom: 40px; background-color: white; padding: 10px; border-radius: 8px;">
                    <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; color: black;">
                        <tr>
                            <th colspan="2" style="border-bottom: 2px solid #555; padding-bottom: 5px; font-size: 18px; text-align: center;">{nome_conta}</th>
                        </tr>
                        <tr>
                            <td style="border-right: 2px solid #555; color: #2e7d32; font-weight: bold; padding: 5px; text-align: right; font-size: 14px;">Débito</td>
                            <td style="color: #c62828; font-weight: bold; padding: 5px; text-align: left; font-size: 14px;">Crédito</td>
                        </tr>
                        {linhas_html}
                        <tr>
                            <td style="border-right: 2px solid #555; border-top: 1px solid #ccc; padding: 5px; font-weight: bold; text-align: right;">Σ {total_debito:,.2f}</td>
                            <td style="border-top: 1px solid #ccc; padding: 5px; font-weight: bold; text-align: left;">Σ {total_credito:,.2f}</td>
                        </tr>
                        <tr>
                            <td colspan="2" style="border-top: 2px solid #555; padding: 10px; font-weight: bold; text-align: center; color: {'#1565c0' if tipo_saldo == 'Devedor' else '#c62828'};">
                                Saldo: {abs(saldo):,.2f} ({tipo_saldo})
                            </td>
                        </tr>
                    </table>
                </div>
                """
                
                # Injeta o HTML renderizado na coluna atual
                with cols[col_idx % 2]:
                    st.markdown(razonete_html, unsafe_allow_html=True)
                col_idx += 1

        # ----------------------------------------
        # VISUALIZAÇÃO DO BALANCETE
        # ----------------------------------------
        with btn_balancete:
            st.subheader("Balancete de Verificação")
            balancete = df.groupby(['grupo', 'nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0.0)
            
            if 'DEBITO' not in balancete.columns: balancete['DEBITO'] = 0.0
            if 'CREDITO' not in balancete.columns: balancete['CREDITO'] = 0.0
            
            balancete['Saldo'] = balancete['DEBITO'] - balancete['CREDITO']
            st.table(balancete)
            
            total_d = balancete['DEBITO'].sum()
            total_c = balancete['CREDITO'].sum()
            
            st.divider()
            if abs(total_d - total_c) < 0.01:
                st.success(f"✅ Sistema Equilibrado! Débitos: R$ {total_d:,.2f} | Créditos: R$ {total_c:,.2f}")
            else:
                st.error(f"❌ Sistema DESEQUILIBRADO! Débitos: R$ {total_d:,.2f} | Créditos: R$ {total_c:,.2f}")

    else:
        st.info("Não há lançamentos ou contas cadastradas para exibir a contabilidade.")

# --- DEMAIS MÓDULOS ---
else:
    st.header(f"Módulo: {menu}")
    st.info("Funcionalidade em desenvolvimento.")
