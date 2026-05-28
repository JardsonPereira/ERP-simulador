import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth

check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📊 DRE Detalhado")

# --- 1. Filtro de Data ---
col1, col2 = st.columns(2)
data_inicio = col1.date_input("Data Início", date(date.today().year, date.today().month, 1))
data_fim = col2.date_input("Data Fim", date.today())

# Busca os dados
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

if res_lanc.data and res_contas.data:
    df_l = pd.DataFrame(res_lanc.data)
    df_c = pd.DataFrame(res_contas.data)
    
    # Merge
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # Conversão de tipos
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
    df['data'] = pd.to_datetime(df['data']) # Certifique-se que sua coluna se chama 'data'
    
    # Aplicação do Filtro
    mask = (df['data'].dt.date >= data_inicio) & (df['data'].dt.date <= data_fim)
    df_filtrado = df.loc[mask]

    # Busca 'grupo' de forma segura
    df_filtrado['grupo'] = df_filtrado.get('grupo_lanc', df_filtrado.get('grupo_conta', 'Outros'))

    # --- 2. Cálculos do DRE ---
    # Nota: Ajuste as strings ('RECEITAS', 'CUSTOS', etc) para o que está salvo no seu banco
    receita_bruta = df_filtrado[df_filtrado['grupo'].str.upper() == 'RECEITAS']['valor'].sum()
    custos = df_filtrado[df_filtrado['grupo'].str.upper() == 'CUSTOS']['valor'].sum()
    despesas_op = df_filtrado[df_filtrado['grupo'].str.upper() == 'DESPESAS_OPERACIONAIS']['valor'].sum()
    despesas_fin = df_filtrado[df_filtrado['grupo'].str.upper() == 'DESPESAS_FINANCEIRAS']['valor'].sum()
    
    lucro_bruto = receita_bruta - custos
    ebitda = lucro_bruto - despesas_op
    lucro_liquido = ebitda - despesas_fin
    
    # --- 3. Exibição ---
    st.subheader(f"Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}")
    
    # Métricas principais
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Receita Bruta", f"R$ {receita_bruta:,.2f}")
    col_b.metric("(-) Custos", f"R$ {custos:,.2f}")
    col_c.metric("(=) Lucro Bruto", f"R$ {lucro_bruto:,.2f}")
    
    st.divider()
    
    col_d, col_e = st.columns(2)
    col_d.metric("(-) Despesas Operacionais", f"R$ {despesas_op:,.2f}")
    col_e.metric("(=) EBITDA", f"R$ {ebitda:,.2f}")
    
    st.divider()
    
    col_f, col_g = st.columns(2)
    col_f.metric("(-) Despesas Financeiras", f"R$ {despesas_fin:,.2f}")
    col_g.metric("(=) Lucro Líquido", f"R$ {lucro_liquido:,.2f}")

else:
    st.info("Nenhum dado encontrado para o período selecionado.")
