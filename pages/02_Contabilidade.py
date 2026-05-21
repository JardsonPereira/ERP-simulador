import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Razonetes")

lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])

    for grupo in sorted(df['grupo'].unique()):
        st.subheader(f"📁 {grupo}")
        df_grupo = df[df['grupo'] == grupo]
        
        for nome_conta in sorted(df_grupo['nome_conta'].unique()):
            d_conta = df_grupo[df_grupo['nome_conta'] == nome_conta]
            
            # Cabeçalho da Conta
            st.markdown(f"**Conta:** {nome_conta}")
            
            # Preparar dados
            deb = d_conta[d_conta['operacao'] == 'DEBITO'][['data_lancamento', 'justificativa', 'valor']]
            cre = d_conta[d_conta['operacao'] == 'CREDITO'][['data_lancamento', 'justificativa', 'valor']]
            
            # Layout em T (Colunas)
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("🟢 Débito")
                if not deb.empty:
                    st.dataframe(deb, hide_index=True, use_container_width=True)
                else: st.caption("Sem débitos")
            
            with col2:
                st.write("🔴 Crédito")
                if not cre.empty:
                    st.dataframe(cre, hide_index=True, use_container_width=True)
                else: st.caption("Sem créditos")
            
            # Saldo Simples
            saldo = deb['valor'].sum() - cre['valor'].sum()
            st.caption(f"Saldo: R$ {saldo:,.2f}")
            st.markdown("---")

else:
    st.info("Sem dados para exibir.")
