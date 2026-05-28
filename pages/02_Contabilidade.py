import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- Inicialização ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Razonetes"

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()
id_to_name = {c['id']: c['nome_conta'] for c in res_contas.data}

if not res_lanc.data:
    st.warning("Nenhum lançamento encontrado.")
    st.stop()

df = pd.DataFrame(res_lanc.data)
df["Conta"] = df["conta_id"].map(id_to_name)

# --- Navegação ---
c1, c2, c3, c4 = st.columns(4)
if c1.button("📂 Plano de Contas", use_container_width=True): st.session_state.view_mode = "Plano de Contas"
if c2.button("📊 Razonetes", use_container_width=True): st.session_state.view_mode = "Razonetes"
if c3.button("📑 Balancete", use_container_width=True): st.session_state.view_mode = "Balancete"
if c4.button("⚖️ Balanço Patrimonial", use_container_width=True): st.session_state.view_mode = "Balanço"

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

# Configuração dos Dataframes
col_config = {
    "data_lancamento": st.column_config.DateColumn("Data", width="small"),
    "valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
    "justificativa": st.column_config.TextColumn("Justif.", width="medium")
}

# --- Exibição ---

if st.session_state.view_mode == "Plano de Contas":
    st.subheader("📂 Estrutura do Plano de Contas")
    df_contas = pd.DataFrame(res_contas.data)
    for grupo in df_contas['grupo'].unique():
        st.markdown(f"**Grupo:** {grupo}")
        contas = df_contas[df_contas['grupo'] == grupo]['nome_conta'].tolist()
        st.write(", ".join(contas))
        st.write("---")

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes: Todos os Lançamentos")
    
    for grupo in df['grupo'].unique():
        st.markdown(f"#### 📂 {grupo}")
        contas = df[df['grupo'] == grupo]['Conta'].unique()
        cols = st.columns(2)
        for i, conta in enumerate(contas):
            df_c = df[(df['grupo'] == grupo) & (df['Conta'] == conta)]
            # Separando e garantindo valores positivos
            deb = df_c[df_c['operacao'] == 'Débito'].copy()
            cred = df_c[df_c['operacao'] == 'Crédito'].copy()
            deb['valor'] = deb['valor'].abs()
            cred['valor'] = cred['valor'].abs()
            
            saldo = deb['valor'].sum() - cred['valor'].sum()
            
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                
                c_d, c_c = st.columns(2)
                with c_d:
                    st.markdown("<p style='text-align:center; color:green; font-weight:bold;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], height=150, hide_index=True, column_config=col_config, use_container_width=True)
                    st.markdown(f"<p class='total-deb'>Total D: R$ {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                with c_c:
                    st.markdown("<p style='text-align:center; color:red; font-weight:bold;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], height=150, hide_index=True, column_config=col_config, use_container_width=True)
                    st.markdown(f"<p class='total-cred'>Total C: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                
                st.markdown(f"<div style='border-top:1px solid #ccc; text-align:center; font-weight:bold;'>SALDO FINAL: R$ {saldo:,.2f}</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df.groupby(['Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    if 'Débito' not in bal.columns: bal['Débito'] = 0.0
    if 'Crédito' not in bal.columns: bal['Crédito'] = 0.0
    bal['Saldo'] = bal['Débito'] - bal['Crédito']
    
    t_deb = bal['Débito'].sum()
    t_cred = bal['Crédito'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Débitos", f"R$ {t_deb:,.2f}")
    c2.metric("Total Créditos", f"R$ {t_cred:,.2f}")
    c3.metric("Diferença", f"R$ {t_deb - t_cred:,.2f}")
    
    st.dataframe(bal, use_container_width=True, column_config={
        "Débito": st.column_config.NumberColumn("Débito (R$)", format="R$ %.2f"),
        "Crédito": st.column_config.NumberColumn("Crédito (R$)", format="R$ %.2f"),
        "Saldo": st.column_config.NumberColumn("Saldo (R$)", format="R$ %.2f")
    })

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    
    # Cálculos agrupados
    a_c = df[(df['grupo']=='Ativo Circulante') & (df['operacao']=='Débito')]['valor'].sum() - df[(df['grupo']=='Ativo Circulante') & (df['operacao']=='Crédito')]['valor'].sum()
    a_nc = df[(df['grupo']=='Ativo Não Circulante') & (df['operacao']=='Débito')]['valor'].sum() - df[(df['grupo']=='Ativo Não Circulante') & (df['operacao']=='Crédito')]['valor'].sum()
    p_c = df[(df['grupo']=='Passivo Circulante') & (df['operacao']=='Crédito')]['valor'].sum() - df[(df['grupo']=='Passivo Circulante') & (df['operacao']=='Débito')]['valor'].sum()
    p_nc = df[(df['grupo']=='Passivo Não Circulante') & (df['operacao']=='Crédito')]['valor'].sum() - df[(df['grupo']=='Passivo Não Circulante') & (df['operacao']=='Débito')]['valor'].sum()
    pl = df[(df['grupo']=='Patrimônio Líquido') & (df['operacao']=='Crédito')]['valor'].sum() - df[(df['grupo']=='Patrimônio Líquido') & (df['operacao']=='Débito')]['valor'].sum()
    
    rec = df[df['grupo']=='Receitas']['valor'].sum()
    desp = df[df['grupo']=='Despesas']['valor'].sum()
    res = rec - desp
    
    tot_a = a_c + a_nc
    tot_p_pl = p_c + p_nc + pl + res
    
    col_a, col_p = st.columns(2)
    with col_a:
        st.markdown("### 🏢 ATIVO")
        st.metric("Total Ativo", f"R$ {tot_a:,.2f}")
        st.write(f"- Ativo Circulante: R$ {a_c:,.2f}")
        st.write(f"- Ativo Não Circulante: R$ {a_nc:,.2f}")
    with col_p:
        st.markdown("### 🏦 PASSIVO + PL")
        st.metric("Total Origens", f"R$ {tot_p_pl:,.2f}")
        st.write(f"- Passivo Circulante: R$ {p_c:,.2f}")
        st.write(f"- Passivo Não Circulante: R$ {p_nc:,.2f}")
        st.write(f"- Patrimônio Líquido: R$ {pl:,.2f}")
        st.write(f"- Resultado do Exercício: R$ {res:,.2f}")

    if abs(tot_a - tot_p_pl) < 0.01:
        st.success("✅ Balanço Equilibrado!")
    else:
        st.error(f"⚠️ Desequilibrado! Diferença: R$ {abs(tot_a - tot_p_pl):,.2f}")
