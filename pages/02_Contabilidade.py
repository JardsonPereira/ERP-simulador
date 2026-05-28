import streamlit as st
import pandas as pd
from datetime import date
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- 1. CARREGAMENTO BLINDADO ---
@st.cache_data(ttl=60)
def carregar_dados():
    res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
    res_contas = supabase.table("contas").select("*").eq("user_id", user_id).execute()
    
    df_lanc = pd.DataFrame(res_lanc.data) if res_lanc.data else pd.DataFrame()
    df_contas = pd.DataFrame(res_contas.data) if res_contas.data else pd.DataFrame()
    
    if df_lanc.empty: return None, None
    
    # Merge garantindo que tudo apareça
    df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
    
    # CRÍTICO: Verificação de segurança para evitar KeyError
    if 'grupo' not in df.columns:
        df['grupo'] = 'SEM CLASSIFICAÇÃO'
    else:
        df['grupo'] = df['grupo'].fillna('SEM CLASSIFICAÇÃO')
        
    df['nome_conta'] = df['nome_conta'].fillna('Conta Sem Nome')
    df['data_lancamento'] = pd.to_datetime(df['data_lancamento']).dt.date
    return df, df_contas

df, df_contas = carregar_dados()

if df is None:
    st.warning("Nenhum lançamento encontrado no banco de dados.")
    st.stop()

# --- 2. CSS PARA RAZONETES ---
st.markdown("""
    <style>
    .t-wrapper { border: 1px solid #999; padding: 10px; margin-bottom: 20px; border-radius: 5px; background: #fff; }
    .t-header { background: #444; color: white; text-align: center; font-weight: bold; padding: 5px; margin-bottom: 10px; }
    .total { font-weight: bold; text-align: right; padding: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. NAVEGAÇÃO ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Razonetes"

c1, c2, c3, c4 = st.columns(4)
if c1.button("📂 Plano de Contas"): st.session_state.view_mode = "Plano"
if c2.button("📊 Razonetes"): st.session_state.view_mode = "Razonetes"
if c3.button("📑 Balancete"): st.session_state.view_mode = "Balancete"
if c4.button("⚖️ Balanço Patrimonial"): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- 4. EXIBIÇÃO ---
if st.session_state.view_mode == "Plano":
    st.subheader("📂 Plano de Contas")
    st.dataframe(df[['nome_conta', 'grupo']].drop_duplicates())

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes Detalhados")
    for g in sorted(df['grupo'].unique()):
        st.markdown(f"### 📂 Grupo: {g}")
        contas = df[df['grupo'] == g]['nome_conta'].unique()
        cols = st.columns(2)
        for i, conta in enumerate(contas):
            c_df = df[(df['grupo'] == g) & (df['nome_conta'] == conta)]
            deb = c_df[c_df['operacao'] == 'Débito']
            cred = c_df[c_df['operacao'] == 'Crédito']
            
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown("<p style='color:green; font-weight:bold;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], hide_index=True, use_container_width=True, height=150)
                    st.markdown(f"<p class='total'>Total D: R$ {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                with d2:
                    st.markdown("<p style='color:red; font-weight:bold;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], hide_index=True, use_container_width=True, height=150)
                    st.markdown(f"<p class='total'>Total C: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                saldo = deb['valor'].sum() - cred['valor'].sum()
                st.markdown(f"<div style
