import streamlit as st
import sys
import os
from datetime import date

# --- CORREÇÃO DO IMPORT ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_supabase, check_auth, show_auth_sidebar

# --- INICIALIZAÇÃO E AUTENTICAÇÃO ---
user = check_auth()
supabase = get_supabase()
show_auth_sidebar(supabase)

user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)

# --- OPÇÕES DO GRUPO CONTÁBIL ---
opcoes_grupo = [
    "Ativo Circulante", 
    "Ativo Não Circulante", 
    "Passivo Circulante", 
    "Passivo Não Circulante", 
    "Patrimônio Líquido", 
    "Receitas", 
    "Despesas", 
    "Transação Interna"
]

# --- INTERFACE PRINCIPAL ---
st.title("💰 Lançamentos nos Razonetes")
st.markdown("Efetue novos lançamentos, edite, exclua ou limpe o histórico.")

# --- CARREGAR CONTAS CADASTRADAS ---
lista_para_selectbox = ["-- Selecionar Conta Existente --"]
dicionario_contas = {}

if user_id:
    try:
        resposta_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
        if resposta_contas.data:
            for conta in resposta_contas.data:
                nome_exibicao = conta["nome_conta"]
                dicionario_contas[nome_exibicao] = conta["id"]
                lista_para_selectbox.append(nome_exibicao)
    except Exception as e:
        st.error(f"Erro ao carregar lista de contas: {e}")

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.form("lancamento_form", clear_on_submit=True):
    st.subheader("📝 Criar Novo Lançamento")
    
    col_conta1, col_conta2 = st.columns(2)
    with col_conta1:
        conta_escolhida = st.selectbox("Selecione uma Conta", lista_para_selectbox)
    with col_conta2:
        nova_conta_nome = st.text_input("OU Digite para CRIAR uma Nova Conta", placeholder="Ex: Banco Inter, Caixa")
    st.markdown("---")

    # Campo de Justificativa adicionado
    justificativa = st.text_input("Justificativa / Histórico", placeholder="Ex: Pagamento de aluguel mensal, Compra de estoque...")
    
    col1, col2 = st.columns(2)
    with col1:
        data_input = st.date_input("Data do Lançamento", date.today())
        valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f") # min_value=0.01 impede negativos na tela
        
    with col2:
        operacao = st.selectbox("Operação", ["Débito", "Crédito"])
        grupo = st.selectbox("Grupo Contábil", opcoes_grupo)
        status = st.selectbox(
            "Status Financeiro", 
            ["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]
        )
        
    submit = st.form_submit_button("Confirmar e Gravar Lançamento")

    # --- LÓGICA DE SALVAMENTO ---
    if submit:
        if conta_escolhida == "-- Selecionar Conta Existente --" and not nova_conta_nome:
            st.warning("Você precisa selecionar uma conta existente OU digitar o nome de uma nova conta!")
        elif not justificativa.strip():
            st.warning("A justificativa é obrigatória!")
        elif not user_id:
            st.error("Sessão inválida. Faça login novamente.")
        else:
            id_real_da_conta = None
            try:
                if nova_conta_nome.strip():
                    dados_nova_conta = {
                        "user_id": user_id,
                        "nome_conta": nova_conta_nome.strip(),
                        "grupo": grupo
                    }
                    resultado_conta = supabase.table("contas").insert(dados_nova_conta).execute()
                    if resultado_conta.data:
                        id_real_da_conta = resultado_conta.data[0]["id"]
                        st.info(f"Nova conta '{nova_conta_nome}' criada com sucesso!")
                else:
                    id_real_da_conta = dicionario_contas[conta_escolhida]

                if id_real_da_conta:
                    dados_lancamento = {
                        "user_id": user_id,
                        "conta_id": id_real_da_conta,
                        "operacao": operacao,
                        "valor": valor, # Agora o valor é salvo estritamente positivo
                        "data_lancamento": str(data_input),
                        "status_financeiro": status,
                        "grupo": grupo,
                        "justificativa": justificativa # Enviando a justificativa
                    }
                    supabase.table("lancamentos").insert(dados_lancamento).execute()
                    st.success("Lançamento registrado com sucesso!")
                    st.rerun() 
            except Exception as e:
                st.error(f"Erro ao processar operação: {e}")

# --- HISTÓRICO DE LANÇAMENTOS ARMAZENADOS (EDIÇÃO E EXCLUSÃO) ---
st.markdown("---")
st.subheader("📊 Histórico e Gerenciamento")

if user_id:
    try:
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()
        
        if response.data:
            st.write("💡 *Dica de Edição: Dê dois cliques em cima de qualquer campo na tabela abaixo para editá-lo diretamente.*")
            
            id_para_nome = {v: k for k, v in dicionario_contas.items()}
            
            dados_com_selecao = []
            for item in response.data:
                item["Excluir"] = False
                item["Conta_Nome"] = id_para_nome.get(item["conta_id"], "Conta Desconhecida")
                dados_com_selecao.append(item)
            
            # Configuração da tabela com a coluna Justificativa
            tabela_editavel = st.data_editor(
                dados_com_selecao,
                use_container_width=True,
                disabled=["id", "user_id", "conta_id", "Conta_Nome"],
                column_order=["Excluir", "data_lancamento", "Conta_Nome", "justificativa", "operacao", "valor", "grupo", "status_financeiro"],
                column_config={
                    "Excluir": st.column_config.CheckboxColumn("🗑️ Excluir?", default=False),
                    "id": None,          
                    "user_id": None,     
                    "conta_id": None, 
                    "Conta_Nome": st.column_config.TextColumn("Conta (Razonete)"),
                    "data_lancamento": st.column_config.TextColumn("Data"),
                    "justificativa": st.column_config.TextColumn("Justificativa"),
                    "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f", min_value=0.01), # Impede edições negativas
                    "operacao": st.column_config.SelectboxColumn("Operação", options=["Débito", "Crédito"]),
                    "grupo": st.column_config.SelectboxColumn("Grupo", options=opcoes_grupo),
                    "status_financeiro": st.column_config.SelectboxColumn("Status", options=["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"])
                }
            )
            
            # --- LÓGICA DE SALVAR EDIÇÕES ---
            if tabela_editavel != dados_com_selecao:
                col_btn1, col_btn2 = st.columns([1, 3])
                with col_btn1:
                    if st.button("💾 Salvar Edições", type="primary"):
                        try:
                            for linha_original, linha_editada in zip(dados_com_selecao, tabela_editavel):
                                if (linha_original["valor"] != linha_editada["valor"] or 
                                    linha_original["operacao"] != linha_editada["operacao"] or 
                                    linha_original["grupo"] != linha_editada["grupo"] or 
                                    linha_original["status_financeiro"] != linha_editada["status_financeiro"] or
                                    linha_original["data_lancamento"] != linha_editada["data_lancamento"] or
                                    linha_original.get("justificativa") != linha_editada.get("justificativa")):
                                    
                                    id_linha = linha_original["id"]
                                    dados_atualizados = {
                                        "data_lancamento": str(linha_editada["data_lancamento"]),
                                        "valor": abs(float(linha_editada["valor"])), # Força ser absoluto/positivo caso tentem burlar
                                        "operacao": linha_editada["operacao"],
                                        "grupo": linha_editada["grupo"],
                                        "status_financeiro": linha_editada["status_financeiro"],
                                        "justificativa": linha_editada.get("justificativa", "")
                                    }
                                    supabase.table("lancamentos").update(dados_atualizados).eq("id", id_linha).execute()
                            st.success("Edições salvas com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar edições: {e}")
                
            # --- LÓGICA DE EXCLUIR SELECIONADOS ---
            ids_para_deletar = [linha["id"] for linha in tabela_editavel if linha["Excluir"]]
            if ids_para_deletar:
                if st.button("🗑️ Confirmar Exclusão", type="primary"):
                    try:
                        supabase.table("lancamentos").delete().in_("id", ids_para_deletar).execute()
                        st.success("Lançamentos excluídos!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")

            # --- LÓGICA DE RESETAR TUDO ---
            st.markdown("---")
            with st.expander("🚨 Zona de Perigo - Resetar Tudo"):
                st.warning("Atenção! Esta ação apagará permanentemente todos os seus lançamentos contábeis. Esta ação não pode ser desfeita.")
                confirmacao = st.text_input("Para confirmar, digite 'DELETAR TUDO' no campo abaixo:")
                
                if st.button("💥 APAGAR TODO O HISTÓRICO"):
                    if confirmacao == "DELETAR TUDO":
                        try:
                            supabase.table("lancamentos").delete().eq("user_id", user_id).execute()
                            st.success("Todo o seu histórico foi resetado com sucesso!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao resetar: {e}")
                    else:
                        st.error("Frase de confirmação incorreta.")
        else:
            st.info("Nenhum lançamento armazenado.")
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
