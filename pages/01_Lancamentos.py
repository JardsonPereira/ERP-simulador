# ... (código anterior igual)

    # 1. Definir a lista de grupos igual à do formulário
    opcoes_grupo = [
        "Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", 
        "Passivo Não Circulante", "Patrimônio Líquido", "Receitas", 
        "Despesas", "Encargos Financeiros", "Transação Interna"
    ]

    # 2. Adicionar o 'grupo' ao DataFrame de exibição
    df_exibicao = df[["id", "data_lancamento", "Conta", "valor", "justificativa", "operacao", "status_financeiro", "grupo"]].copy()
    
    # 3. Editor de dados com a coluna 'grupo' configurada
    edited_df = st.data_editor(
        df_exibicao, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "valor": st.column_config.NumberColumn("Valor (R$)", format="%.2f"),
            "data_lancamento": st.column_config.DateColumn("Data"),
            "Conta": st.column_config.TextColumn("Conta", disabled=True),
            "operacao": st.column_config.SelectboxColumn("Operação", options=["Débito", "Crédito"]),
            "status_financeiro": st.column_config.SelectboxColumn("Status", options=["Entrada", "Saída", "Pendente", "Investimento", "Transação Interna"]),
            "grupo": st.column_config.SelectboxColumn("Grupo", options=opcoes_grupo) # Adicionado aqui
        }
    )

    if st.button("💾 Salvar Alterações"):
        for i, row in edited_df.iterrows():
            if not row.equals(df_exibicao.iloc[i]):
                supabase.table("lancamentos").update({
                    "valor": float(row["valor"]),
                    "justificativa": row["justificativa"],
                    "status_financeiro": row["status_financeiro"],
                    "operacao": row["operacao"],
                    "grupo": row["grupo"] # Adicionado aqui
                }).eq("id", row["id"]).execute()
        st.success("Alterações salvas!")
        st.rerun()
