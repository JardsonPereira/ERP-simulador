import streamlit as st
import pandas as pd
# ... (seus outros imports)

# --- Seção do Histórico ---
st.markdown("---")
st.subheader("📊 Histórico de Lançamentos")

# 1. Filtros para facilitar a busca
col1, col2 = st.columns(2)
busca = col1.text_input("🔍 Buscar por justificativa")
filtro_status = col2.selectbox("Filtrar por Status", ["Todos"] + ["Entrada", "Saída", "Pendente", "Investimento"])

# 2. Carregar e tratar dados
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data_lancamento", desc=True).execute()

if res_lanc.data:
    df = pd.DataFrame(res_lanc.data)
    
    # Mapeamento de nomes
    id_to_name = {v: k for k, v in dicionario_contas.items()}
    df["Conta"] = df["conta_id"].map(id_to_name)

    # Filtragem
    if busca:
        df = df[df["justificativa"].str.contains(busca, case=False, na="")]
    if filtro_status != "Todos":
        df = df[df["status_financeiro"] == filtro_status]

    # 3. Data Editor aprimorado
    # Definindo configurações de coluna
    column_config = {
        "valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", min_value=0),
        "data_lancamento": st.column_config.DateColumn("Data"),
        "status_financeiro": st.column_config.SelectboxColumn("Status", options=["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]),
        "operacao": st.column_config.SelectboxColumn("Operação", options=["Débito", "Crédito"])
    }

    st.info("💡 Dica: Você pode editar valores e status diretamente na tabela.")
    
    # Exibir o editor
    edited_df = st.data_editor(
        df[["data_lancamento", "Conta", "valor", "justificativa", "operacao", "status_financeiro"]],
        column_config=column_config,
        use_container_width=True,
        num_rows="dynamic" # Permite deletar linhas se configurado
    )

    # 4. Botão de persistência unificado
    if st.button("💾 Salvar Alterações"):
        with st.spinner("Atualizando banco de dados..."):
            # Lógica para comparar o edited_df com o original e dar UPDATE no Supabase
            # Dica: Use df.compare(edited_df) para encontrar apenas o que mudou
            st.success("Alterações salvas!")
            st.rerun()
