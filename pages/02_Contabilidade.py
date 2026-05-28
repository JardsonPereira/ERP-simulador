import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
st.title("📈 Demonstrações Contábeis")

# --- Inicialização de Estado ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Razonetes"

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta").eq("user_id", user_id).execute()
id_to_name = {c['id']: c['nome_conta'] for c in res_contas.data}

if not res_lanc.data:
    st.warning("Nenhum lançamento encontrado para gerar as demonstrações.")
    st.stop()

df = pd.DataFrame(res_lanc.data)
df["Conta"] = df["conta_id"].map(id_to_name)

# --- Navegação ---
col1, col2, col3 = st.columns(3)
if col1.button("📊 Razonetes (Demonstração Detalhada)", use_container_width=True): st.session_state.view_mode = "Razonetes"
if col2.button("📑 Balancete (Totais)", use_container_width=True): st.session_state.view_mode = "Balancete"
if col3.button("⚖️ Balanço Patrimonial", use_container_width=True): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Exibição ---

if st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes: Demonstração de Movimentações")
    
    st.markdown("""
        <style>
        .t-account { border: 2px solid #333; border-radius: 5px; padding: 10px; margin-bottom: 20px; background-color: #fcfcfc; max-width: 900px; }
        .vertical-line { border-right: 2px solid #333; }
        </style>
    """, unsafe_allow_html=True)
    
    col_config = {
        "data_lancamento": st.column_config.DateColumn("Data", width="small"),
        "valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
        "justificativa": st.column_config.TextColumn("Justificativa", width="medium")
    }

    grupos = df['grupo'].unique()
    for grupo in grupos:
        st.markdown(f"### 📂 Grupo: {grupo}")
        df_grupo = df[df['grupo'] == grupo]
        
        for conta in df_grupo['Conta'].unique():
            df_conta = df_grupo[df_grupo['Conta'] == conta]
            deb = df_conta[df_conta['operacao'] == 'Débito']
            cred = df_conta[df_conta['operacao'] == 'Crédito']
            saldo_valor = deb['valor'].sum() - cred['valor'].sum()
            
            # Natureza do Saldo
            if saldo_valor > 0:
                label_saldo = f"SALDO DEVEDOR: R$ {saldo_valor:,.2f}"
                bg_color = "green"
            elif saldo_valor < 0:
                label_saldo = f"SALDO CREDOR: R$ {abs(saldo_valor):,.2f}"
                bg_color = "red"
            else:
                label_saldo = "SALDO ZERADO: R$ 0.00"
                bg_color = "black"

            st.markdown('<div class="t-account">', unsafe_allow_html=True)
            st.markdown(f"<div style='background-color: black; color: white; padding: 5px; text-align: center; font-weight: bold; border-bottom: 2px solid #333;'>{conta.upper()}</div>", unsafe_allow_html=True)
            
            c_t1, c_t2 = st.columns(2)
            with c_t1:
                st.markdown("<div class='vertical-line'><h6 style='color: green; text-align: center;'>Débito</h6>", unsafe_allow_html=True)
                st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], use_container_width=True, height=100, hide_index=True, column_config=col_config)
                st.markdown(f"<p style='color: green; font-weight: bold; text-align: right; padding-right: 15px;'>Total D: R$ {deb['valor'].sum():,.2f}</p></div>", unsafe_allow_html=True)
            with c_t2:
                st.markdown("<h6 style='color: red; text-align: center;'>Crédito</h6>", unsafe_allow_html=True)
                st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], use_container_width=True, height=100, hide_index=True, column_config=col_config)
                st.markdown(f"<p style='color: red; font-weight: bold; text-align: right; padding-right: 15px;'>Total C: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='background-color: {bg_color}; color: white; padding: 5px; text-align: center; font-weight: bold;'>{label_saldo}</div>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df.groupby(['Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo Devedor'] = bal.apply(lambda row: row['Débito'] - row['Crédito'] if row['Débito'] > row['Crédito'] else 0, axis=1)
    bal['Saldo Credor'] = bal.apply(lambda row: row['Crédito'] - row['Débito'] if row['Crédito'] > row['Débito'] else 0, axis=1)
    
    t_devedor = bal['Saldo Devedor'].sum()
    t_credor = bal['Saldo Credor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Saldo Devedor", f"R$ {t_devedor:,.2f}")
    m2.metric("Total Saldo Credor", f"R$ {t_credor:,.2f}")
    m3.metric("Diferença", f"R$ {t_devedor - t_credor:,.2f}")
    
    st.markdown("---")
    st.dataframe(bal[['Saldo Devedor', 'Saldo Credor']], use_container_width=True, column_config={
        "Saldo Devedor": st.column_config.NumberColumn(format="R$ %.2f"),
        "Saldo Credor": st.column_config.NumberColumn(format="R$ %.2f")
    })

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    ativo = df[df['grupo'].str.contains('Ativo', na=False)]['valor'].sum()
    passivo = df[df['grupo'].str.contains('Passivo', na=False)]['valor'].sum()
    pl = df[df['grupo'] == 'Patrimônio Líquido']['valor'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Ativo", f"R$ {ativo:,.2f}")
    m2.metric("Total Passivo", f"R$ {passivo:,.2f}")
    m3.metric("PL", f"R$ {pl:,.2f}")
    
    if abs(ativo - (passivo + pl)) < 0.01:
        st.success("✅ Balanço Patrimonial Equilibrado!")
    else:
        st.error(f"⚠️ Balanço Desequilibrado! Diferença: R$ {abs(ativo - (passivo + pl)):,.2f}")
