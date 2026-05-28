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

# --- Inicialização ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Plano de Contas"

# --- Dados ---
res_lanc = supabase.table("lancamentos").select("*").eq("user_id", user_id).execute()
res_contas = supabase.table("contas").select("id, nome_conta, grupo").eq("user_id", user_id).execute()
id_to_name = {c['id']: c['nome_conta'] for c in res_contas.data}
id_to_group = {c['id']: c['grupo'] for c in res_contas.data}

if not res_lanc.data:
    st.warning("Nenhum lançamento encontrado.")
    st.stop()

df = pd.DataFrame(res_lanc.data)
df["Conta"] = df["conta_id"].map(id_to_name)
df["grupo"] = df["conta_id"].map(id_to_group)
# Garantir formato de data
df["data_lancamento"] = pd.to_datetime(df["data_lancamento"]).dt.date

# --- Filtro de Data ---
st.sidebar.header("🗓️ Filtros")
data_inicio = st.sidebar.date_input("Data Início", value=date(2026, 1, 1))
data_fim = st.sidebar.date_input("Data Fim", value=date.today())

# Aplica o filtro
mask = (df["data_lancamento"] >= data_inicio) & (df["data_lancamento"] <= data_fim)
df_filtered = df.loc[mask]

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
    .t-wrapper { border: 1px solid #ccc; padding: 10px; margin-bottom: 20px; border-radius: 8px; background: #fff; }
    .t-header { background: #333; color: white; text-align: center; font-weight: bold; padding: 5px; border-radius: 4px; margin-bottom: 5px; }
    .total-deb { color: green; font-size: 1em; font-weight: bold; text-align: right; }
    .total-cred { color: red; font-size: 1em; font-weight: bold; text-align: right; }
    .saldo-box { border-top: 2px solid #333; text-align: center; font-weight: bold; font-size: 1.1em; padding-top: 5px; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- Função de Cálculo ---
def get_group_details(group_name, nature):
    df_g = df_filtered[df_filtered['grupo'] == group_name]
    if df_g.empty: return 0.0, {}
    # Agrupa por conta e soma valores
    accounts = df_g.groupby('Conta')['valor'].sum().to_dict()
    d = df_g[df_g['operacao'] == 'Débito']['valor'].sum()
    c = df_g[df_g['operacao'] == 'Crédito']['valor'].sum()
    total = (d - c) if nature == 'D' else (c - d)
    return total, accounts

# --- Abas ---
if st.session_state.view_mode == "Plano de Contas":
    st.subheader("📂 Estrutura do Plano de Contas")
    df_contas = pd.DataFrame(res_contas.data)
    for grupo in df_contas['grupo'].unique():
        st.markdown(f"**Grupo:** {grupo}")
        contas = df_contas[df_contas['grupo'] == grupo]['nome_conta'].tolist()
        st.write(", ".join(contas))
        st.write("---")

elif st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes por Grupo")
    
    natureza_devedora = ['Ativo Circulante', 'Ativo Não Circulante', 'Despesas']
    
    col_config = {
        "data_lancamento": st.column_config.DateColumn("Data", width="small"),
        "valor": st.column_config.NumberColumn("Valor", width="small", format="R$ %.2f"),
        "justificativa": st.column_config.TextColumn("Justif.", width="medium")
    }
    
    grupos_unicos = df_filtered['grupo'].unique()
    
    for grupo in grupos_unicos:
        st.markdown("---")
        st.markdown(f"### 📁 {grupo}")
        
        contas_do_grupo = df_filtered[df_filtered['grupo'] == grupo]['Conta'].unique()
        cols = st.columns(2)
        
        for i, conta in enumerate(contas_do_grupo):
            df_c = df_filtered[df_filtered['Conta'] == conta]
            grupo_conta = df_c['grupo'].iloc[0]
            
            deb = df_c[df_c['operacao'] == 'Débito'].copy()
            cred = df_c[df_c['operacao'] == 'Crédito'].copy()
            
            d_total = deb['valor'].sum()
            c_total = cred['valor'].sum()
            
            if grupo_conta in natureza_devedora:
                saldo = d_total - c_total
                tipo_saldo = "Saldo Devedor"
            else:
                saldo = c_total - d_total
                tipo_saldo = "Saldo Credor"
                
            with cols[i % 2]:
                st.markdown('<div class="t-wrapper">', unsafe_allow_html=True)
                st.markdown(f'<div class="t-header">{conta.upper()}</div>', unsafe_allow_html=True)
                
                c_d, c_c = st.columns(2)
                with c_d:
                    st.markdown("<p style='text-align:center; color:green; font-weight:bold;'>Débito</p>", unsafe_allow_html=True)
                    st.dataframe(deb[['data_lancamento', 'valor', 'justificativa']], height=150, hide_index=True, column_config=col_config, use_container_width=True)
                    st.markdown(f"<p class='total-deb'>Total D: R$ {d_total:,.2f}</p>", unsafe_allow_html=True)
                with c_c:
                    st.markdown("<p style='text-align:center; color:red; font-weight:bold;'>Crédito</p>", unsafe_allow_html=True)
                    st.dataframe(cred[['data_lancamento', 'valor', 'justificativa']], height=150, hide_index=True, column_config=col_config, use_container_width=True)
                    st.markdown(f"<p class='total-cred'>Total C: R$ {c_total:,.2f}</p>", unsafe_allow_html=True)
                
                st.markdown(f'<div class="saldo-box">{tipo_saldo}: R$ {saldo:,.2f}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df_filtered.groupby(['Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
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
    
    # 1. Obter saldos das contas patrimoniais
    a_c, a_c_accts = get_group_details('Ativo Circulante', 'D')
    a_nc, a_nc_accts = get_group_details('Ativo Não Circulante', 'D')
    p_c, p_c_accts = get_group_details('Passivo Circulante', 'C')
    p_nc, p_nc_accts = get_group_details('Passivo Não Circulante', 'C')
    pl, pl_accts = get_group_details('Patrimônio Líquido', 'C')
    
    # 2. Calcular o ARE (Apuração do Resultado do Exercício)
    rec, _ = get_group_details('Receitas', 'C')
    desp, _ = get_group_details('Despesas', 'D')
    resultado_exercicio = rec - desp
    
    # 3. Consolidar os Totais
    tot_a = a_c + a_nc
    # O PL agora incorpora o resultado do exercício
    pl_final = pl + resultado_exercicio
    tot_p_pl = p_c + p_nc + pl_final
    
    # 4. Exibição
    col_a, col_p = st.columns(2)
    
    with col_a:
        st.markdown("### 🏢 ATIVO")
        st.metric("Total Ativo", f"R$ {tot_a:,.2f}")
        for g, accts in [('Ativo Circulante', a_c_accts), ('Ativo Não Circulante', a_nc_accts)]:
            st.markdown(f"**{g}**")
            for acc, v in accts.items(): st.write(f"- {acc}: R$ {v:,.2f}")
            
    with col_p:
        st.markdown("### 🏦 PASSIVO + PL")
        st.metric("Total Origens", f"R$ {tot_p_pl:,.2f}")
        
        # Passivo
        for g, accts in [('Passivo Circulante', p_c_accts), ('Passivo Não Circulante', p_nc_accts)]:
            st.markdown(f"**{g}**")
            for acc, v in accts.items(): st.write(f"- {acc}: R$ {v:,.2f}")
            
        # Patrimônio Líquido incorporando a ARE
        st.markdown("**Patrimônio Líquido**")
        for acc, v in pl_accts.items(): 
            st.write(f"- {acc}: R$ {v:,.2f}")
        
        # Exibe o resultado como parte do PL
        label_resultado = "Lucro do Exercício" if resultado_exercicio >= 0 else "Prejuízo do Exercício"
        st.write(f"- **{label_resultado}: R$ {resultado_exercicio:,.2f}**")
        st.markdown(f"---")
        st.write(f"**Total do PL Consolidado: R$ {pl_final:,.2f}**")

    # Validação de Equilíbrio
    if abs(tot_a - tot_p_pl) < 0.01:
        st.success("✅ Balanço Equilibrado!")
    else:
        st.error(f"⚠️ Desequilibrado! Diferença: R$ {abs(tot_a - tot_p_pl):,.2f}")
