elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")

    # 1. Agrupar dados: Somar os totais de Débito e Crédito por conta
    # Unstack transforma as linhas 'Débito' e 'Crédito' em colunas
    bal = df.groupby(['grupo', 'Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    
    # Garantir que as colunas existam
    if 'Débito' not in bal.columns: bal['Débito'] = 0.0
    if 'Crédito' not in bal.columns: bal['Crédito'] = 0.0
    
    # 2. Calcular Saldo Devedor e Credor separadamente
    # Lógica: Se Débito > Crédito, o saldo é Devedor. Se Crédito > Débito, é Credor.
    bal['Saldo Devedor'] = bal.apply(lambda x: x['Débito'] - x['Crédito'] if x['Débito'] > x['Crédito'] else 0.0, axis=1)
    bal['Saldo Credor'] = bal.apply(lambda x: x['Crédito'] - x['Débito'] if x['Crédito'] > x['Débito'] else 0.0, axis=1)
    
    # 3. Calcular totais para as métricas superiores
    total_devedor = bal['Saldo Devedor'].sum()
    total_credor = bal['Saldo Credor'].sum()
    
    # 4. Exibir Métricas de Conferência
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Saldo Devedor", f"R$ {total_devedor:,.2f}")
    c2.metric("Total Saldo Credor", f"R$ {total_credor:,.2f}")
    
    # Conferência de diferença
    diferenca = total_devedor - total_credor
    c3.metric("Diferença (D-C)", f"R$ {diferenca:,.2f}", delta_color="inverse")
    
    st.markdown("---")
    
    # 5. Exibição da Tabela Final
    # Selecionamos apenas as colunas de saldo para simplificar a visualização
    st.dataframe(
        bal[['Saldo Devedor', 'Saldo Credor']],
        use_container_width=True,
        column_config={
            "Saldo Devedor": st.column_config.NumberColumn("Saldo Devedor (R$)", format="R$ %.2f"),
            "Saldo Credor": st.column_config.NumberColumn("Saldo Credor (R$)", format="R$ %.2f"),
        }
    )
    
    # 6. Validação Visual
    if abs(diferenca) < 0.01:
        st.success("✅ Balancete validado: O total de saldos devedores e credores está igual.")
    else:
        st.error(f"⚠️ Atenção: Balancete desequilibrado! Diferença de R$ {abs(diferenca):,.2f}.")
