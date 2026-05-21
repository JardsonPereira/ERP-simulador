import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ERP Didático Integrado", layout="wide")

# Inicialização Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error(f"Erro ao conectar ao Supabase: {e}")
    st.stop()

# --- LÓGICA DE NEGÓCIO (INTEGRAÇÃO) ---
def processar_venda_integrada(produto_id, qtd, valor_venda):
    # Busca dados atuais
    prod = supabase.table("produtos").select("*").eq("id", produto_id).single().execute()
    regra = supabase.table("config_tributaria").select("*").eq("categoria", prod.data['categoria']).single().execute()
    
    prod_data = prod.data
    regra_data = regra.data
    
    total_bruto = qtd * valor_venda
    imposto = total_bruto * (regra_data['aliquota_icms'] + regra_data['aliquota_iss'])
    valor_liquido = total_bruto - imposto
    
    # 1. Registrar Nota Fiscal
    supabase.table("notas_fiscais").insert({
        "tipo": "Saida", "produto_id": produto_id, "quantidade": qtd,
        "valor_unitario": valor_venda, "valor_total_bruto": total_bruto, "valor_imposto": imposto
    }).execute()
    
    # 2. Lançamento Contábil
    supabase.table("lancamentos").insert([
        {"natureza": "Receita", "descricao": f"VENDA - {prod_data['nome']}", "tipo": "Crédito", "valor": valor_liquido, "status": "Pago"},
        {"natureza": "Passivo Circulante", "descricao": f"IMPOSTO {prod_data['nome']}", "tipo": "Crédito", "valor": imposto, "status": "Pendente"}
    ]).execute()
    
    # 3. Baixa no Estoque (WMS)
    supabase.table("produtos").update({"saldo_estoque": prod_data['saldo_estoque'] - qtd}).eq("id", produto_id).execute()

# --- INTERFACE ---
st.title("🏢 ERP Acadêmico: Integração de Setores")
menu = st.sidebar.radio("Navegação", ["🛒 Vendas (Integrado)", "📦 Estoque (WMS)", "📊 Contabilidade"])

# A. MÓDULO DE VENDAS
if menu == "🛒 Vendas (Integrado)":
    st.header("🛒 Ponto de Venda")
    resp = supabase.table("produtos").select("*").execute()
    produtos = resp.data
    
    if not produtos:
        st.warning("Cadastre produtos no menu Estoque primeiro!")
    else:
        with st.form("venda_form"):
            p_sel = st.selectbox("Produto", [p['nome'] for p in produtos])
            qtd = st.number_input("Quantidade", min_value=1, step=1)
            if st.form_submit_button("Confirmar Venda"):
                prod = next(p for p in produtos if p['nome'] == p_sel)
                if prod['saldo_estoque'] >= qtd:
                    processar_venda_integrada(prod['id'], qtd, prod['preco_venda'])
                    st.success("Venda integrada com sucesso!")
                else:
                    st.error("Saldo insuficiente!")

# B. MÓDULO DE ESTOQUE
elif menu == "📦 Estoque (WMS)":
    st.header("📦 Gestão de Estoque")
    df_prod = pd.DataFrame(supabase.table("produtos").select("*").execute().data)
    
    if not df_prod.empty:
        # Exibe a tabela apenas se as colunas existirem
        colunas_exibir = ['nome', 'categoria', 'preco_venda', 'saldo_estoque']
        st.table(df_prod[colunas_exibir])
    
    with st.expander("Cadastrar Novo Produto"):
        with st.form("add_prod"):
            nome = st.text_input("Nome")
            cat = st.selectbox("Categoria", ["Produtos", "Serviços"])
            preco = st.number_input("Preço Venda")
            if st.form_submit_button("Salvar"):
                supabase.table("produtos").insert({"nome": nome, "categoria": cat, "preco_venda": preco, "saldo_estoque": 100}).execute()
                st.rerun()

# C. MÓDULO CONTÁBIL
elif menu == "📊 Contabilidade":
    st.header("📊 Razonetes Contábeis")
    data = supabase.table("lancamentos").select("*").execute().data
    if data:
        df_lanc = pd.DataFrame(data)
        st.dataframe(df_lanc[['descricao', 'natureza', 'tipo', 'valor']])
    else:
        st.info("Nenhum lançamento contábil encontrado.")
