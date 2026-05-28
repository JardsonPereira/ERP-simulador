import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="Contabilidade Compacta")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- Inicialização ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Razonetes"

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
id_to_name = {c['id']: c['nome_conta'] for c in res_contas.data}

if not res_lanc.data:
    st.warning("Nenhum lançamento encontrado.")
    st.stop()

df = pd.DataFrame(res_lanc.data)
df["Conta"] = df["conta_id"].map(id_to_name)

# --- Navegação ---
col1, col2, col3 = st.columns(3)
if col1.button("📊 Razonetes", use_container_width=True): st.session_state.view_mode = "Razonetes"
if col2.button("📑 Balancete", use_container_width=True): st.session_state.view_mode = "Balancete"
if col3.button("⚖️ Balanço", use_container_width=True): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Estilos CSS para Compactar ---
st.markdown("""
    <style>
    .t-account { border: 1px solid #ccc; padding: 5px; margin-bottom: 10px; border-radius: 4px; background: #fafafa; }
    .t-header { background: #333; color: white; text-align: center; font-weight: bold; padding: 2px; border-radius: 2px; }
    .total-text { font-size: 0.8em; font-weight: bold; text-align: right; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# --- Exibição ---

if st.session_state.view_mode == "Razonetes":
    col_config = {
        "data_lancamento": st.column_config.DateColumn("Data", width="small"),
        "valor": st.column_config.NumberColumn("Valor", width="small", format="%.2f"),
        "justificativa": st.column_config.TextColumn("Justif.", width="medium")
    }

    grupos = df['grupo'].unique()
    for grupo in grupos:
        st.markdown(f"#### 📂 {grupo}")
        df_grupo = df[df['grupo'] == grupo]
        
        for conta in df_grupo['Conta'].unique():
            df_conta = df_grupo[df_grupo['Conta'] == conta]
            deb = df_conta[df_conta['operacao'] == 'Débito']
            cred = df_conta[df_conta['operacao'] == 'Crédito']
            saldo_v = deb['valor'].sum() - cred['valor'].sum()
            
            # Formatação do saldo
            cor_saldo = "green" if saldo_v > 0 else ("red" if saldo_v < 0 else "black")
            texto_saldo = f"SALDO: R$ {saldo_v:,.2f}"

            st.markdown('<div class="t-account">', unsafe_allow_html=True)
            st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<p style='text-align:center; color:green; margin:0;'>Débito</p>", unsafe_allow_html=True)
                st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], 
                             use_container_width=True, height=70, hide_index=True, column_config=col_config)
                st.markdown(f"<p class='total-text' style='color:green;'>Total D: {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
            
            with c2:
                st.markdown("<p style='text-align:center; color:red; margin:0;'>Crédito</p>", unsafe_allow_html=True)
                st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], 
                             use_container_width=True, height=70, hide_index=True, column_config=col_config)
                st.markdown(f"<p class='total-text' style='color:red;'>Total C: {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='border-top:1px solid #ccc; text-align:center; font-weight:bold; color:{cor_saldo};'>{texto_saldo}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df.groupby(['Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo Devedor'] = bal.apply(lambda r: r['Débito'] - r['Crédito'] if r['Débito'] > r['Crédito'] else 0, axis=1)
    bal['Saldo Credor'] = bal.apply(lambda r: r['Crédito'] - r['Débito'] if r['Crédito'] > r['Débito'] else 0, axis=1)
    
    t_d, t_c = bal['Saldo Devedor'].sum(), bal['Saldo Credor'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Devedor", f"R$ {t_d:,.2f}")
    c2.metric("Saldo Credor", f"R$ {t_c:,.2f}")
    c3.metric("Diferença", f"R$ {t_d - t_c:,.2f}")
    
    st.dataframe(bal[['Saldo Devedor', 'Saldo Credor']], use_container_width=True)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    ativo = df[df['grupo'].str.contains('Ativo', na=False)]['valor'].sum()
    passivo = df[df['grupo'].str.contains('Passivo', na=False)]['valor'].sum()
    pl = df[df['grupo'] == 'Patrimônio Líquido']['valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Ativo", f"R$ {ativo:,.2f}")
    m2.metric("Total Passivo + PL", f"R$ {passivo + pl:,.2f}")
    
    if abs(ativo - (passivo + pl)) < 0.01:
        st.success("Equilibrado!")
    else:
        st.error(f"Desequilibrado! Diferença: {abs(ativo - (passivo + pl)):,.2f}")
