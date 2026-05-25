import streamlit as st

# Proteção de página: redireciona se não estiver logado
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Acesso não autorizado. Por favor, faça o login.")
    st.stop()  # Impede que o restante do código seja carregado

# --- Seu código existente da página começa aqui ---
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
from utils import get_data_cached, check_auth, inject_css, gerar_relatorio_pdf

check_auth(); inject_css()
st.header("📈 DRE")
lancamentos = get_data_cached("lancamentos", st.session_state.user.id)
contas = get_data_cached("contas", st.session_state.user.id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento'])
    c1, c2 = st.columns(2)
    d_i = c1.date_input("Início", value=df['data_lancamento'].min().date())
    d_f = c2.date_input("Fim", value=df['data_lancamento'].max().date())
    df_dre = df[(df['data_lancamento'].dt.date >= d_i) & (df['data_lancamento'].dt.date <= d_f)]
    
    receita_bruta = df_dre[df_dre['grupo'] == 'RECEITAS']['valor'].sum()
    cmv = df_dre[df_dre['grupo'] == 'CMV']['valor'].sum()
    despesas = df_dre[df_dre['grupo'] == 'DESPESAS']['valor'].sum()
    encargos = df_dre[df_dre['grupo'] == 'ENCARGOS FINANCEIROS']['valor'].sum()
    
    dre_data = pd.DataFrame({"Descrição": ["(+) Receita Bruta", "(-) CMV", "(=) Lucro Bruto", "(-) Despesas", "(-) Encargos", "(=) Lucro Líquido"],
                            "Valor": [receita_bruta, cmv, receita_bruta - cmv, despesas, encargos, (receita_bruta - cmv - despesas - encargos)]})
    st.table(dre_data.set_index("Descrição").style.format("R$ {:,.2f}"))
    if st.download_button("Baixar DRE PDF", data=gerar_relatorio_pdf("DRE", dre_data), file_name="dre.pdf"): st.success("Download iniciado!")
