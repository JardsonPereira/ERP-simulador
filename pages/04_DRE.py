import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth

# --- Configuração Inicial ---
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.set_page_config(page_title="DRE Detalhado", layout="wide")
st.title("📊 DRE - Demonstração do Resultado")

# --- 1. Filtro de Data ---
col1, col2 = st.columns(2)
data_inicio = col1.date_input("Data Início", date(date.today().year, date.today().month, 1))
data_fim = col2.date_input("Data Fim", date.today())

# --- 2. Busca e Preparação dos Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

if res_lanc.data and res_contas.data:
    df_l = pd.DataFrame(res_lanc.data)
    df_c = pd.DataFrame(res_contas.data)
    
    # Merge das tabelas
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # Detecção inteligente da coluna de data
    possiveis_colunas_data = ['data', 'data_lancamento', 'created_at', 'data_transacao']
    coluna_data = next((col for col in df.columns if col in possiveis_colunas_data), None)
    
    if coluna_data:
        df['data_formatada'] = pd.to_datetime(df[coluna_data])
    else:
        st.error(f"Erro: Coluna de data não encontrada. Colunas: {list(df.columns)}")
        st.stop()

    # Conversão de valores
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Identificação do grupo
    coluna_grupo = 'grupo_lanc' if 'grupo_lanc' in df.columns else 'grupo_conta'
    
    # Aplicação do Filtro
    mask = (df['data_formatada'].dt.date >= data_inicio) & (df['data_formatada'].dt.date <= data_fim)
    df_filtrado = df.loc[mask].copy()

    # --- 3. Categorização e Cálculos ---
    # Normalização
    df_filtrado['grupo_upper'] = df_filtrado[coluna_grupo].str.upper()

    # Definição de quais nomes no banco pertencem a cada grupo
    # Ajuste essas listas caso os nomes no banco sejam diferentes
    map_receitas = ['RECEITA', 'RECEITAS', 'ENTRADA']
    map_despesas = ['DESPESA', 'DESPESAS', 'DESPESAS OPERACIONAIS', 'DESPESA OPERACIONAL']
    map_encargos = ['ENCARGO', 'ENCARGOS', 'DESPESAS DE ENCARGOS', 'DESPESAS FINANCEIRAS', 'FINANCEIRO']
    
    # Cálculos
    receita_bruta = df_filtrado[df_filtrado['grupo_upper'].isin(map_receitas)]['valor'].sum()
    despesas_op = df_filtrado[df_filtrado['grupo_upper'].isin(map_despesas)]['valor'].sum()
    despesas_encargos = df_filtrado[df_filtrado['grupo_upper'].isin(map_encargos)]['valor'].sum()
    
    ebitda = receita_bruta - despesas_op
    lucro_liquido = ebitda - despesas_encargos
    
    # --- 4. Exibição ---
    st.subheader(f"Período: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")
    
    c1, c2 = st.columns(2)
    c1.metric("Receita Bruta", f"R$ {receita_bruta:,.2f}")
    c2.metric("(-) Despesas Operacionais", f"R$ {despesas_op:,.2f}")
    
    st.divider()
    
    c3, c4 = st.columns(2)
    c3.metric("(=) EBITDA", f"R$ {ebitda:,.2f}")
    c4.metric("(-) Despesas de Encargos", f"R$ {despesas_encargos:,.2f}")
    
    st.divider()
    
    st.metric("(=) Lucro Líquido", f"R$ {lucro_liquido:,.2f}", delta_color="normal")

else:
    st.info("Nenhum dado encontrado para gerar o DRE.")
