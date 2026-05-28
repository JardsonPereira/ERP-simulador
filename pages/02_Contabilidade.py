elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes por Grupo")
    
    natureza_devedora = ['Ativo Circulante', 'Ativo Não Circulante', 'Despesas']
    
    col_config = {
        "data_lancamento": st.column_config.DateColumn("Data", width="small"),
        "valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
        "justificativa": st.column_config.TextColumn("Justif.", width="medium")
    }
    
    # 1. Pegamos todos os grupos únicos presentes no filtro atual
    grupos_unicos = df_filtered['grupo'].unique()
    
    # 2. Loop pelos Grupos
    for grupo in grupos_unicos:
        st.markdown(f"---")
        st.markdown(f"### 📁 {grupo}")
        
        # Filtra apenas contas deste grupo
        contas_do_grupo = df_filtered[df_filtered['grupo'] == grupo]['Conta'].unique()
        
        # Cria colunas para as contas dentro deste grupo
        cols = st.columns(2)
        
        for i, conta in enumerate(contas_do_grupo):
            # Filtra lançamentos da conta específica
            df_c = df_filtered[df_filtered['Conta'] == conta]
            grupo_conta = df_c['grupo'].iloc[0]
            
            deb = df_c[df_c['operacao'] == 'Débito'].copy()
            cred = df_c[df_c['operacao'] == 'Crédito'].copy()
            
            deb['valor'] = deb['valor'].abs()
            cred['valor'] = cred['valor'].abs()
            
            d_total = deb['valor'].sum()
            c_total = cred['valor'].sum()
            
            # Cálculo de Saldo
            if grupo_conta in natureza_devedora:
                saldo = d_total - c_total
                tipo_saldo = "Saldo Devedor"
            else:
                saldo = c_total - d_total
                tipo_saldo = "Saldo Credor"
                
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                
                c_d, c_c = st.columns(2)
                with c_d:
                    st.markdown("<p style='text-align:center; color:green; font-weight:bold;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], height=150, hide_index=True, column_config=col_config, use_container_width=True)
                    st.markdown(f"<p class='total-deb'>Total D: R$ {d_total:,.2f}</p>", unsafe_allow_html=True)
                with c_c:
                    st.markdown("<p style='text-align:center; color:red; font-weight:bold;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], height=150, hide_index=True, column_config=col_config, use_container_width=True)
                    st.markdown(f"<p class='total-cred'>Total C: R$ {c_total:,.2f}</p>", unsafe_allow_html=True)
                
                st.markdown(f'<div class="saldo-box">{tipo_saldo}: R$ {saldo:,.2f}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
