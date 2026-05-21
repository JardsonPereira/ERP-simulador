import pandas as pd

def processar_venda_integrada(supabase, user_id, produto_id, qtd, valor_venda):
    prod = supabase.table("produtos").select("*").eq("id", produto_id).single().execute().data
    regra = supabase.table("config_tributaria").select("*").eq("categoria", prod['categoria']).single().execute().data
    
    valor_bruto = qtd * valor_venda
    imposto = valor_bruto * (regra['aliquota_icms'] + regra['aliquota_iss'])
    
    # Grava na contabilidade
    supabase.table("lancamentos").insert([
        {"user_id": user_id, "descricao": f"VENDA {prod['nome']}", "natureza": "Receita", "tipo": "Crédito", "valor": valor_bruto - imposto},
        {"user_id": user_id, "descricao": f"IMPOSTO {prod['nome']}", "natureza": "Passivo Circulante", "tipo": "Crédito", "valor": imposto}
    ]).execute()
    
    # Baixa estoque
    supabase.table("produtos").update({"saldo_estoque": prod['saldo_estoque'] - qtd}).eq("id", produto_id).execute()
