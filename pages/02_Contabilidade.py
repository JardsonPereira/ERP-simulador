elif st.session_state.view_mode == "Balancete":

    st.subheader("📑 Balancete de Verificação")



    # 1. Preparação dos dados para o Balancete

    # Criamos uma tabela dinâmica (pivot) para somar Débitos e Créditos por conta

    balancete = df.groupby(['grupo', 'Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)

    

    # Garantir que as colunas existam, mesmo que não haja lançamentos

    if 'Débito' not in balancete.columns: balancete['Débito'] = 0.0

    if 'Crédito' not in balancete.columns: balancete['Crédito'] = 0.0

    

    # Calcular Saldo

    balancete['Saldo'] = balancete['Débito'] - balancete['Crédito']

    

    # 2. Métricas de Conferência (Cabeçalho)

    t_deb = balancete['Débito'].sum()

    t_cred = balancete['Crédito'].sum()

    

    c1, c2, c3 = st.columns(3)

    c1.metric("Total Débitos", f"R$ {t_deb:,.2f}")

    c2.metric("Total Créditos", f"R$ {t_cred:,.2f}")

    c3.metric("Diferença", f"R$ {t_deb - t_cred:,.2f}", delta_color="inverse")

    

    st.markdown("---")

    

    # 3. Exibição da Tabela Estilizada

    # Usamos o column_config para formatar como moeda e alinhar

    st.dataframe(

        balancete,

        use_container_width=True,

        column_config={

            "Débito": st.column_config.NumberColumn("Total Débitos (R$)", format="R$ %.2f"),

            "Crédito": st.column_config.NumberColumn("Total Créditos (R$)", format="R$ %.2f"),

            "Saldo": st.column_config.NumberColumn("Saldo Líquido (R$)", format="R$ %.2f"),

            "grupo": "Grupo Contábil"

        }

    )

    

    # 4. Validação Visual

    if abs(t_deb - t_cred) < 0.01:

        st.success("✅ Balancete validado: Débitos e Créditos estão iguais.")

    else:

        st.error("⚠️ Atenção: O balancete não está fechado. A soma dos débitos deve ser igual à dos créditos.")  
