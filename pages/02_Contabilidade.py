import streamlit as st
import pandas as pd
from utils import get_supabase, check_auth

# --- Configuração ---
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
    st.warning("Nenhum lançamento encontrado para gerar as demonstrações.")
    st.stop()

df = pd.DataFrame(res_lanc.data)
df["Conta"] = df["conta_id"].map(id_to_name)

# --- Navegação ---
col1, col2, col3 = st.columns(3)
if col1.button("📊 Razonetes", use_container_width=True): st.session_state.view_mode = "Razonetes"
if col2.button("📑 Balancete", use_container_width=True): st.session_state.view_mode = "Balancete"
if col3.button("⚖️ Balanço Patrimonial", use_container_width=True): st.session_state.view_mode = "Balanço"

st.markdown("---")

# --- Exibição ---

if st.session_state.view_mode == "Razonetes":
    st.subheader("📊 Razonetes (Livro Razão em T)")
    
    grupos = df['grupo'].unique()
    for grupo in grupos:
        st.markdown(f"### 📂 Grupo: {grupo}")
        df_grupo = df[df['grupo'] == grupo]
        
        for conta in df_grupo['Conta'].unique():
            df_conta = df_grupo[df_grupo['Conta'] == conta]
            deb = df_conta[df_conta['operacao'] == 'Débito']
            cred = df_conta[df_conta['operacao'] == 'Crédito']
            saldo = deb['valor'].sum() - cred['valor'].sum()
            
            # Cabeçalho da Conta (Preto/Branco)
            st.markdown(f"""
                <div style="background-color: black; color: white; padding: 3px; text-align: center; font-weight: bold; border-radius: 5px; margin-bottom: 2px; font-size: 0.9em;">
                    {conta}
                </div>
            """, unsafe_allow_html=True)
            
            c_t1, c_t2 = st.columns(2)
            
            # Débito (Verde) - Compacto com Justificativa
            with c_t1:
                st.markdown("<h6 style='color: green; text-align: center; margin: 0;'>Débito</h6>", unsafe_allow_html=True)
                st.dataframe(
                    deb[['data_lancamento', 'valor', 'justificativa']], 
                    use_container_width=True, 
                    height=80, 
                    hide_index=True
                )
                st.markdown(f"<p style='color: green; font-weight: bold; margin: 0; font-size: 0.8em;'>Total: R$ {deb['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
            
            # Crédito (Vermelho) - Compacto com Justificativa
            with c_t2:
                st.markdown("<h6 style='color: red; text-align: center; margin: 0;'>Crédito</h6>", unsafe_allow_html=True)
                st.dataframe(
                    cred[['data_lancamento', 'valor', 'justificativa']], 
                    use_container_width=True, 
                    height=80, 
                    hide_index=True
                )
                st.markdown(f"<p style='color: red; font-weight: bold; margin: 0; font-size: 0.8em;'>Total: R$ {cred['valor'].sum():,.2f}</p>", unsafe_allow_html=True)
            
            # Saldo Final (Preto/Branco)
            st.markdown(f"""
                <div style="background-color: black; color: white; padding: 3px; text-align: center; border-radius: 5px; margin-top: 5px; margin-bottom: 20px; font-weight: bold;">
                    SALDO FINAL: R$ {saldo:,.2f}
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.view_mode == "Balancete":
    st.subheader("📑 Balancete de Verificação")
    bal = df.groupby(['Conta', 'operacao'])['valor'].sum().unstack(fill_value=0)
    bal['Saldo'] = bal.get('Débito', 0) - bal.get('Crédito', 0)
    st.dataframe(bal, use_container_width=True)

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
