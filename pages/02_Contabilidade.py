import streamlit as st, pandas as pd, sys, os

# Configuração de caminho
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_supabase, get_data_cached, check_auth, inject_css

check_auth(); inject_css(); supabase = get_supabase()

st.header("📚 Razonetes Compactos")

lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    
    # Filtro
    d_inicio = st.date_input("Início", value=df['data_lancamento'].min().date())
    mask = (df['data_lancamento'].dt.date >= d_inicio)
    df_p = df[mask]

    for grupo in sorted(df_p['grupo'].unique()):
        st.subheader(f"📁 {grupo}")
        for nome_conta in sorted(df_p[df_p['grupo'] == grupo]['nome_conta'].unique()):
            d_c = df_p[df_p['nome_conta'] == nome_conta]
            
            # Cabeçalho da conta centralizado e discreto
            st.markdown(f"<div style='text-align:center; font-weight:bold; background:#f0f2f6; padding:5px; border-radius:5px;'>{nome_conta}</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Função para renderizar lançamentos de forma compacta
            def listar_lancamentos(df_tipo):
                for _, row in df_tipo.iterrows():
                    # Formato compacto: Data - R$ Valor - (Justificativa)
                    st.markdown(f"<small>📅 {row['data_lancamento'].strftime('%d/%m')}: <b>R$ {row['valor']:,.2f}</b><br><i>{row['justificativa']}</i></small>", unsafe_allow_html=True)
            
            with col1:
                st.markdown("<center>🟢 DÉBITO</center>", unsafe_allow_html=True)
                listar_lancamentos(d_c[d_c['operacao'] == 'DEBITO'])
            with col2:
                st.markdown("<center>🔴 CRÉDITO</center>", unsafe_allow_html=True)
                listar_lancamentos(d_c[d_c['operacao'] == 'CREDITO'])
            
            # Resumo do saldo (Mais compacto)
            saldo = d_c[d_c['operacao'] == 'DEBITO']['valor'].sum() - d_c[d_c['operacao'] == 'CREDITO']['valor'].sum()
            st.markdown(f"<div style='text-align:center; font-size:0.9em; margin-top:5px;'>Saldo: <b>R$ {saldo:,.2f}</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

else:
    st.info("Sem dados.")
