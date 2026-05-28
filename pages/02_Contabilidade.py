import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
st.set_page_config(layout="wide", page_title="ContabilApp - Contabilidade")
check_auth()
supabase = get_supabase()
user_id = st.session_state.user.id

st.title("📈 Demonstrações Contábeis")

# --- Inicialização de Estado ---
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
if col3.button("⚖️ Balanço Patrimonial", use_container_width=True): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Estilos CSS ---
st.markdown("""
    <style>
    .t-wrapper { border: 1px solid #ccc; padding: 5px; margin-bottom: 10px; border-radius: 4px; background: #fafafa; }
    .t-header { background: #333; color: white; text-align: center; font-weight: bold; padding: 2px; border-radius: 2px; }
    .total-text { font-size: 0.8em; font-weight: bold; text-align: right; margin: 0; }
    </style>
""", unsafe_allow_html=True)

col_config_geral = {
    "valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
    "data_lancamento": st.column_config.DateColumn("Data", width="small"),
    "justificativa": st.column_config.TextColumn("Justif.", width="medium")
}

# --- Exibição ---

if st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes: Demonstração Detalhada")
    grupos = df['grupo'].unique()
    for grupo in grupos:
        st.markdown(f"#### 📂 {grupo}")
        contas = df[df['grupo'] == grupo]['Conta'].unique()
        cols = st.columns(2)
        for i, conta in enumerate(contas):
            df_conta = df[(df['grupo'] == grupo) & (df['Conta'] == conta)]
            deb = df_conta[df_conta['operacao'] == 'Débito']
            cred = df_conta[df_conta['operacao'] == 'Crédito']
            saldo_v = deb['valor'].sum() - cred['valor'].sum()
            
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("<p style='text-align:center; color:green; margin:0;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], height=70, hide_index=True, column_config=col_config_geral, use_container_width=True)
                    st.markdown(f"<p class='total-text' style='color:green;'>Total D: R$ {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                with c2:
                    st.markdown("<p style='text-align:center; color:red; margin:0;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], height=70, hide_index=True, column_config=col_config_geral, use_container_width=True)
                    st.markdown(f"<p class='total-text' style='color:red;'>Total C: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<div style='border-top:1px solid #ccc; text-align:center; font-weight:bold;'>SALDO: R$ {saldo_v:,.2f}</div>", unsafe_allow_html=True)
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
    st.markdown("### Estrutura: Ativo = Passivo + PL + Resultado")
    
    def get_saldo(grupo, nat='D'):
        df_g = df[df['grupo'] == grupo]
        deb = df_g[df_g['operacao'] == 'Débito']['valor'].sum()
        cred = df_g[df_g['operacao'] == 'Crédito']['valor'].sum()
        return (deb - cred) if nat == 'D' else (cred - deb)

    a_circ, a_nao_circ = get_saldo('Ativo Circulante', 'D'), get_saldo('Ativo Não Circulante', 'D')
    p_circ, p_nao_circ = get_saldo('Passivo Circulante', 'C'), get_saldo('Passivo Não Circulante', 'C')
    pl_base = get_saldo('Patrimônio Líquido', 'C')
    resultado = get_saldo('Receitas', 'C') - get_saldo('Despesas', 'D')
    
    col_a, col_p = st.columns(2)
    with col_a:
        st.markdown("### 🏢 ATIVO")
        st.metric("Total Ativo", f"R$ {a_circ + a_nao_circ:,.2f}")
        st.write(f"- Circulante: R$ {a_circ:,.2f} | Não Circ.: R$ {a_nao_circ:,.2f}")
    with col_p:
        st.markdown("### 🏦 PASSIVO + PL")
        st.metric("Total Passivo + PL + Res.", f"R$ {p_circ + p_nao_circ + pl_base + resultado:,.2f}")
        st.write(f"- Passivo: R$ {p_circ + p_nao_circ:,.2f}")
        st.write(f"- PL + Resultado: R$ {pl_base + resultado:,.2f}")

    if abs((a_circ + a_nao_circ) - (p_circ + p_nao_circ + pl_base + resultado)) < 0.01:
        st.success("✅ Balanço Equilibrado!")
    else:
        st.error("⚠️ Balanço Desequilibrado!")
