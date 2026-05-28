import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="Contabilidade Compacta")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Razonetes (Livro Razão)")

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
id_to_name = {c['id']: c['nome_conta'] for c in res_contas.data}

if not res_lanc.data:
    st.warning("Nenhum lançamento encontrado.")
    st.stop()

df = pd.DataFrame(res_lanc.data)
df["Conta"] = df["conta_id"].map(id_to_name)

# --- Estilos CSS para o Formato T ---
st.markdown("""
    <style>
    .t-wrapper {
        border: 2px solid #333;
        padding: 5px;
        margin-bottom: 20px;
        border-radius: 5px;
        background-color: #fcfcfc;
    }
    .t-header {
        background-color: #333;
        color: white;
        text-align: center;
        font-weight: bold;
        padding: 5px;
        margin-bottom: 5px;
    }
    .t-divider {
        border-right: 2px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# --- Exibição Agrupada ---
grupos = df['grupo'].unique()

for grupo in grupos:
    st.markdown(f"### 📁 Grupo: {grupo}")
    
    # Criar colunas para exibir razonetes lado a lado (2 por linha)
    contas_do_grupo = df[df['grupo'] == grupo]['Conta'].unique()
    
    # Exibir em grade de 2 colunas para aproveitar o espaço
    cols = st.columns(2)
    
    for i, conta in enumerate(contas_do_grupo):
        # Filtra dados da conta
        df_conta = df[(df['grupo'] == grupo) & (df['Conta'] == conta)]
        deb = df_conta[df_conta['operacao'] == 'Débito']
        cred = df_conta[df_conta['operacao'] == 'Crédito']
        
        # Desenha o Razonete
        with cols[i % 2]:
            st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
            st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
            
            c_int1, c_int2 = st.columns(2)
            
            # Coluna Débito
            with c_int1:
                st.markdown('<div class="t-divider">', unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:green; margin:0;'>Débito</p>", unsafe_allow_html=True)
                st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], 
                             use_container_width=True, height=100, hide_index=True)
                st.markdown(f"<p style='font-size:0.8em; color:green; text-align:right;'>Total: {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Coluna Crédito
            with c_int2:
                st.markdown("<p style='text-align:center; color:red; margin:0;'>Crédito</p>", unsafe_allow_html=True)
                st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], 
                             use_container_width=True, height=100, hide_index=True)
                st.markdown(f"<p style='font-size:0.8em; color:red; text-align:right;'>Total: {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
            
            # Saldo
            saldo = deb['valor'].sum() - cred['valor'].sum()
            st.markdown(f"<div style='border-top:2px solid #333; text-align:center; font-weight:bold;'>Saldo: {saldo:,.2f}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
