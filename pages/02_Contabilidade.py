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
    st.session_state.view_mode = "Plano de Contas"

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
    .total-text { font-size: 0.8em; font-weight: bold; text-align: right; margin: 0; }
    </style>
""", unsafe_allow_html=True)

# --- Funções Auxiliares ---
def get_group_balance(group_name, nature='D'):
    """Calcula o saldo de um grupo de contas. 
    Natureza D (Ativos/Despesas) ou C (Passivos/PL/Receitas)."""
    df_g = df[df['grupo'] == group_name]
    if df_g.empty: return 0.0
    
    d = df_g[df_g['operacao'] == 'Débito']['valor'].sum()
    c = df_g[df_g['operacao'] == 'Crédito']['valor'].sum()
    
    return (d - c) if nature == 'D' else (c - d)

# --- Exibição das Abas ---

if st.session_state.view_mode == "Plano de Contas":
    st.subheader("📂 Estrutura do Plano de Contas")
    df_contas = pd.DataFrame(res_contas.data)
    for grupo in df_contas['grupo'].unique():
        st.markdown(f"**Grupo:** {grupo}")
        contas = df_contas[df_contas['grupo'] == grupo]['nome_conta'].tolist()
        st.write(", ".join(contas))
        st.write("---")

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes: Demonstração Detalhada")
    col_config = {"data_lancamento": st.column_config.DateColumn("Data", width="small"),
                  "valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
                  "justificativa": st.column_config.TextColumn("Justif.", width="medium")}
    
    for grupo in df['grupo'].unique():
        st.markdown(f"#### 📂 {grupo}")
        contas = df[df['grupo'] == grupo]['Conta'].unique()
        cols = st.columns(2)
        for i, conta in enumerate(contas):
            df_c = df[(df['grupo'] == grupo) & (df['Conta'] == conta)]
            deb = df_c[df_c['operacao'] == 'Débito']
            cred = df_c[df_c['operacao'] == 'Crédito']
            saldo = deb['valor'].sum() - cred['valor'].sum()
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                c_d, c_c = st.columns(2)
                with c_d:
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], height=70, hide_index=True, column_config=col_config, use_container_width=True)
                with c_c:
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], height=70, hide_index=True, column_config=col_config, use_container_width=True)
                st.markdown(f"<div style='text-align:center; font-weight:bold;'>SALDO: R$ {saldo:,.2f}</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df.groupby(['Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.dataframe(bal, use_container_width=True, column_config={
        "Débito": st.column_config.NumberColumn("Débito (R$)", format="R$ %.2f"),
        "Crédito": st.column_config.NumberColumn("Crédito (R$)", format="R$ %.2f"),
        "Saldo": st.column_config.NumberColumn("Saldo (R$)", format="R$ %.2f")
    })

elif st.session_state.view_mode == "Balanço":
    st.subheader("⚖️ Balanço Patrimonial")
    
    # Agregação dos Razonetes (Grupos)
    a_circ = get_group_balance('Ativo Circulante', 'D')
    a_nao_circ = get_group_balance('Ativo Não Circulante', 'D')
    
    p_circ = get_group_balance('Passivo Circulante', 'C')
    p_nao_circ = get_group_balance('Passivo Não Circulante', 'C')
    pl_base = get_group_balance('Patrimônio Líquido', 'C')
    
    # Resultado (Receitas - Despesas)
    receitas = get_group_balance('Receitas', 'C')
    despesas = get_group_balance('Despesas', 'D')
    resultado = receitas - despesas
    
    tot_ativo = a_circ + a_nao_circ
    tot_passivo_pl = p_circ + p_nao_circ + pl_base + resultado
    
    # Exibição
    col_a, col_p = st.columns(2)
    with col_a:
        st.markdown("### 🏢 ATIVO")
        st.metric("Total Ativo", f"R$ {tot_ativo:,.2f}")
        st.write(f"- Ativo Circulante: R$ {a_circ:,.2f}")
        st.write(f"- Ativo Não Circulante: R$ {a_nao_circ:,.2f}")
        
    with col_p:
        st.markdown("### 🏦 PASSIVO + PL")
        st.metric("Total Passivo + PL", f"R$ {tot_passivo_pl:,.2f}")
        st.write(f"- Passivo Circulante: R$ {p_circ:,.2f}")
        st.write(f"- Passivo Não Circulante: R$ {p_nao_circ:,.2f}")
        st.write(f"- Patrimônio Líquido: R$ {pl_base:,.2f}")
        st.write(f"- Resultado do Exercício: R$ {resultado:,.2f}")

    if abs(tot_ativo - tot_passivo_pl) < 0.01:
        st.success("✅ Balanço Patrimonial Equilibrado!")
    else:
        st.error(f"⚠️ Balanço Desequilibrado! Diferença: R$ {abs(tot_ativo - tot_passivo_pl):,.2f}")
