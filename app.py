# --- FUNÇÕES DE RELATÓRIO COM FILTRO E PARTIDA DOBRADA ---
def mostrar_sistema(user_id, email_usuario):
    # Carrega dados
    lanc = supabase.table("lancamentos").select("*").execute().data
    df = pd.DataFrame(lanc) if lanc else pd.DataFrame()
    if not df.empty:
        df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])

    menu = st.sidebar.radio("Navegação", ["🛒 Lançamentos", "📊 Razonetes", "🧾 Balancete", "📈 DRE"])

    if menu == "🛒 Lançamentos":
        # ... (seu formulário de lançamento)
        
    elif menu == "📊 Razonetes":
        st.header("📊 Razonetes (Partidas Dobradas)")
        st.info("Visualização no formato de Partidas Dobradas: Débitos vs Créditos.")
        
        # Agrupamento visual para Razonete
        for natureza, grupo in df.groupby('natureza'):
            st.write(f"### Conta: {natureza}")
            # Divide em colunas para mostrar a natureza da partida
            col_deb, col_cred = st.columns(2)
            with col_deb:
                st.write("**Débitos**")
                st.table(grupo[grupo['tipo'] == 'Débito'][['descricao', 'valor']])
            with col_cred:
                st.write("**Créditos**")
                st.table(grupo[grupo['tipo'] == 'Crédito'][['descricao', 'valor']])

    elif menu == "🧾 Balancete":
        st.header("🧾 Balancete por Período")
        col1, col2 = st.columns(2)
        data_ini = col1.date_input("Data Início")
        data_fim = col2.date_input("Data Fim")
        
        # Filtro de período
        mask = (df['data_lancamento'].dt.date >= data_ini) & (df['data_lancamento'].dt.date <= data_fim)
        df_filtrado = df.loc[mask]
        
        st.table(df_filtrado.groupby(['natureza', 'tipo'])['valor'].sum().unstack(fill_value=0))
