import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()

df_lanc = pd.DataFrame(res_lanc.data)
df_contas = pd.DataFrame(res_contas.data)

# Merging para garantir que o grupo está em todos os lançamentos
df = pd.merge(df_lanc, df_contas, left_on='conta_id', right_on='id', how='left')
df['grupo'] = df['grupo'].fillna('Sem Grupo')
df['nome_conta'] = df['nome_conta'].fillna('Conta Não Encontrada')

# --- Navegação ---
if 'view_mode' not in st.session_state: st.session_state.view_mode = "Auditoria"

c1, c2, c3, c4, c5 = st.columns(5)
if c1.button("🔍 Auditoria", use_container_width=True): st.session_state.view_mode = "Auditoria"
if c2.button("📂 Plano de Contas", use_container_width=True): st.session_state.view_mode = "Plano de Contas"
if c3.button("📊 Razonetes", use_container_width=True): st.session_state.view_mode = "Razonetes"
if c4.button("📑 Balancete", use_container_width=True): st.session_state.view_mode = "Balancete"
if c5.button("⚖️ Balanço Patrimonial", use_container_width=True): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Estilos CSS ---
st.markdown("""
    <style>
    .t-wrapper { border: 1px solid #ccc; padding: 5px; margin-bottom: 10px; border-radius: 4px; background: #fafafa; }
    .t-header { background: #333; color: white; text-align: center; font-weight: bold; padding: 2px; border-radius: 2px; }
    .total-deb { color: green; font-size: 0.9em; font-weight: bold; text-align: right; }
    .total-cred { color: red; font-size: 0.9em; font-weight: bold; text-align: right; }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def get_group_details(group_name, nature):
    df_g = df[df['grupo'] == group_name]
    if df_g.empty: return 0.0, {}
    accounts = df_g.groupby('nome_conta')['valor'].agg(['sum']).to_dict()['sum']
    d = df_g[df_g['operacao'] == 'Débito']['valor'].sum()
    c = df_g[df_g['operacao'] == 'Crédito']['valor'].sum()
    total = (d - c) if nature == 'D' else (c - d)
    return total, accounts

# --- Lógica das Abas ---

if st.session_state.view_mode == "Auditoria":
    st.subheader("🔍 Auditoria de Dados")
    st.info("Esta aba mostra o porquê dos valores divergirem.")
    
    # 1. Contas sem grupo
    no_group = df[df['grupo'] == 'Sem Grupo']
    if not no_group.empty:
        st.warning(f"⚠️ {len(no_group)} lançamentos estão em contas SEM GRUPO definido!")
        st.dataframe(no_group[['nome_conta', 'valor', 'justificativa']])
    else:
        st.success("✅ Todas as contas possuem grupo definido.")

elif st.session_state.view_mode == "Plano de Contas":
    st.subheader("📂 Estrutura do Plano de Contas")
    for grupo in df['grupo'].unique():
        st.markdown(f"**{grupo}**")
        contas = df[df['grupo'] == grupo]['nome_conta'].unique()
        st.write(", ".join(contas))

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes")
    for grupo in df['grupo'].unique():
        st.markdown(f"#### 📂 {grupo}")
        contas = df[df['grupo'] == grupo]['nome_conta'].unique()
        cols = st.columns(2)
        for i, conta in enumerate(contas):
            df_c = df[(df['grupo'] == grupo) & (df['nome_conta'] == conta)]
            deb = df_c[df_c['operacao'] == 'Débito'].copy()
            cred = df_c[df_c['operacao'] == 'Crédito'].copy()
            saldo = deb['valor'].sum() - cred['valor'].sum()
            
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                c_d, c_c = st.columns(2)
                with c_d:
                    st.markdown("<p style='text-align:center; color:green; font-weight:bold;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['valor', 'justificativa']], height=70, hide_index=True, use_container_width=True)
                    st.markdown(f"<p class='total-deb'>Total D: R$ {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                with c_c:
                    st.markdown("<p style='text-align:center; color:red; font-weight:bold;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['valor', 'justificativa']], height=70, hide_index=True, use_container_width=True)
                    st.markdown(f"<p class='total-cred'>Total C: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-weight:bold;'>SALDO: R$ {saldo:,.2f}</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete")
    bal = df.groupby(['nome_conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    t_deb, t_cred = bal.get('Débito', 0).sum(), bal.get('Crédito', 0).sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Débitos", f"R$ {t_deb:,.2f}")
    c2.metric("Créditos", f"R$ {t_cred:,.2f}")
    c3.metric("Diferença", f"R$ {t_deb - t_cred:,.2f}")
    st.dataframe(bal, use_container_width=True)

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    # Agregação
    a_c, a_c_accts = get_group_details('Ativo Circulante', 'D')
    a_nc, a_nc_accts = get_group_details('Ativo Não Circulante', 'D')
    p_c, p_c_accts = get_group_details('Passivo Circulante', 'C')
    p_nc, p_nc_accts = get_group_details('Passivo Não Circulante', 'C')
    pl, pl_accts = get_group_details('Patrimônio Líquido', 'C')
    res = get_group_details('Receitas', 'C')[0] - get_group_details('Despesas', 'D')[0]
    
    tot_a = a_c + a_nc
    tot_p_pl = p_c + p_nc + pl + res
    
    col_a, col_p = st.columns(2)
    with col_a:
        st.markdown("### 🏢 ATIVO")
        for g, accts in [('Ativo Circulante', a_c_accts), ('Ativo Não Circulante', a_nc_accts)]:
            st.markdown(f"**{g}**"); 
            for acc, v in accts.items(): st.write(f"- {acc}: R$ {v:,.2f}")
    with col_p:
        st.markdown("### 🏦 PASSIVO + PL")
        for g, accts in [('Passivo Circulante', p_c_accts), ('Passivo Não Circulante', p_nc_accts), ('Patrimônio Líquido', pl_accts)]:
            st.markdown(f"**{g}**"); 
            for acc, v in accts.items(): st.write(f"- {acc}: R$ {v:,.2f}")
        st.markdown(f"**Resultado:** R$ {res:,.2f}")

    if abs(tot_a - tot_p_pl) < 0.01: st.success("✅ Equilibrado!")
    else: st.error(f"⚠️ Diferença: R$ {abs(tot_a - tot_p_pl):,.2f}")
