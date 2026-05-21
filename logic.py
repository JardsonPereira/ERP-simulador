import streamlit as st

def processar_venda(supabase, produto_id, qtd, valor_unitario):
    # 1. Buscar dados e regras
    prod = supabase.table("produtos").select("*").eq("id", produto_id).single().execute()
    regra = supabase.table("config_tributaria").select("*").eq("categoria", prod.data['categoria']).single().execute()
    
    total_bruto = qtd * valor_unitario
    imposto = total_bruto * (regra.data['aliquota_icms'] + regra.data['aliquota_iss'])
    
    # 2. Registrar Nota Fiscal
    supabase.table("notas_fiscais").insert({
        "tipo": "Saida", "produto_id": produto_id, "quantidade": qtd,
        "valor_total": total_bruto, "imposto_total": imposto
    }).execute()
    
    # 3. Lançamento Contábil (Débito: Caixa / Crédito: Receita e Impostos)
    supabase.table("lancamentos").insert([
        {"natureza": "Receita", "descricao": f"VENDA {prod.data['nome']}", "tipo": "Crédito", "valor": total_bruto - imposto},
        {"natureza": "Passivo Circulante", "descricao": "IMPOSTO A RECOLHER", "tipo": "Crédito", "valor": imposto}
    ]).execute()
    
    # 4. Baixa Estoque (WMS)
    supabase.table("produtos").update({"saldo_estoque": prod.data['saldo_estoque'] - qtd}).eq("id", produto_id).execute()
