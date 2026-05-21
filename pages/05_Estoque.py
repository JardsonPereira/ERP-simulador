import streamlit as st, pandas as pd, sys, os

# 1. Configurar o caminho para encontrar o utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Importar as funções
from utils import get_supabase, get_data_cached, check_auth, inject_css

# 3. Executar configurações iniciais
check_auth()      # Verifica o login
inject_css()      # Aplica o estilo
supabase = get_supabase() # <--- ISTO CRIA A VARIÁVEL

# A partir daqui, pode usar 'supabase' livremente no seu código
# Exemplo: lancamentos = supabase.table("lancamentos").select("*").execute()
import streamlit as st, pandas as pd, sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth(); inject_css()
st.header("📦 Movimentação de Estoque")
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df_est = df[df['grupo'] == 'ATIVO CIRCULANTE ESTOQUE'].copy()
    total_entradas = df_est[df_est['operacao'] == 'DEBITO']['valor'].sum()
    total_saidas = df_est[df_est['operacao'] == 'CREDITO']['valor'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Entradas", f"R$ {total_entradas:,.2f}")
    c2.metric("Saídas", f"R$ {total_saidas:,.2f}")
    c3.metric("Saldo", f"R$ {total_entradas - total_saidas:,.2f}")
    st.table(df_est[['data_lancamento', 'nome_conta', 'operacao', 'valor']])
else: st.info("Nenhuma movimentação de estoque registrada.")
