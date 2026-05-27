import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📊 DRE - Demonstração do Resultado")

# Busca os dados
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()

if res_lanc.data and res_contas.data:
    df_l = pd.DataFrame(res_lanc.data)
    df_c = pd.DataFrame(res_contas.data)
    
    # Merge com tratamento de colunas
    df = df_l.merge(df_c, left_on='conta_id', right_on='id', suffixes=('_lanc', '_conta'))
    
    # --- CORREÇÃO DO KEYERROR ---
    # Busca 'grupo' de forma segura, independente do nome que o merge deu
    df['grupo'] = df.get('grupo_lanc', df.get('grupo_conta', 'Outros'))
    
    # Converter valor para numérico
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

    # Filtros de Categoria (Assumindo que os nomes no seu banco são 'RECEITAS', 'DESPESAS', etc)
    # Ajuste os nomes conforme o que você gravou no banco
    receitas = df[df['grupo'].str.upper() == 'RECEITAS']['valor'].sum()
    custos = df[df['grupo'].str.upper() == 'CUSTOS']['valor'].sum()
    despesas = df[df['grupo'].str.upper() == 'DESPESAS']['valor'].sum()
    
    lucro_bruto = receitas - custos
    lucro_liquido = lucro_bruto - despesas
    
    # Exibição
    st.metric("Receita Bruta", f"R$ {receitas:,.2f}")
    st.metric("Custos", f"R$ {custos:,.2f}")
    st.markdown("---")
    st.metric("Lucro Bruto", f"R$ {lucro_bruto:,.2f}")
    st.metric("Despesas", f"R$ {despesas:,.2f}")
    st.markdown("---")
    st.metric("Lucro Líquido", f"R$ {lucro_liquido:,.2f}", delta_color="normal")

else:
    st.info("Nenhum dado encontrado para gerar o DRE.")
