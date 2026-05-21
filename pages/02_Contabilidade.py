import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

# Inicialização
check_auth()
inject_css()
supabase = get_supabase()

st.header("📚 Razonetes por Grupo")

# Carregar Dados
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Filtro de Período
    c1, c2 = st.columns(2)
    d_inicio = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    mask_periodo = (df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)
    
    # Estilização das Justificativas (CSS Discreto)
    st.markdown("""
        <style>
        .justificativa { font-size: 0.8em; color: #7f8c8d; font-style: italic; }
        </style>
    """, unsafe_allow_html=True)

    # LOOP PRINCIPAL: Agrupamento
    for grupo in sorted(df['grupo'].unique()):
        st.markdown(f"## 📁 Grupo: {grupo}")
        df_grupo = df[(df['grupo'] == grupo) & mask_periodo]
        
        # LOOP SECUNDÁRIO: Contas do grupo
        for nome_conta in sorted(df_grupo['nome_conta'].unique()):
            d_conta = df_grupo[df_grupo['nome_conta'] == nome_conta]
            
            st.markdown(f"### {nome_conta}")
            
            # Preparação dos dados para a tabela
            def preparar_tabela(tipo):
                sub = d_conta[d_conta['operacao'] == tipo].copy()
                if sub.empty: return pd.DataFrame(columns=['Data', 'Justificativa', 'Valor'])
                
                # Formatação "discreta" da justificativa usando HTML
                sub['justificativa'] = sub['justificativa'].apply(lambda x: f"<span class='justificativa'>{x}</span>")
                return sub[['data_lancamento', 'justificativa', 'valor']]

            deb_df = preparar_tabela('DEBITO')
            cre_df = preparar_tabela('CREDITO')
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown("<div style='background-color:#e8f5e9; padding:5px; border-radius:5px 5px 0 0; text-align:center;'><strong>DÉBITO</strong></div>", unsafe_allow_html=True)
                st.write(deb_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            with col_t2:
                st.markdown("<div style='background-color:#ffebee; padding:5px; border-radius:5px 5px 0 0; text-align:center;'><strong>CRÉDITO</strong></div>", unsafe_allow_html=True)
                st.write(cre_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # Saldo
            saldo = d_conta[d_conta['operacao'] == 'DEBITO']['valor'].sum() - d_conta[d_conta['operacao'] == 'CREDITO']['valor'].sum()
            st.info(f"Saldo da conta {nome_conta}: **R$ {saldo:,.2f}**")
            st.divider()

else:
    st.info("Sem dados para exibir.")
