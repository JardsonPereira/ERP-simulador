def processar_venda_integrada(supabase, produto_id, qtd, valor_venda):
    # 1. Busca dados do produto e regra fiscal
    prod = supabase.table("produtos").select("*").eq("id", produto_id).single().execute()
    regra = supabase.table("config_tributaria").select("*").eq("categoria", prod.data['categoria']).single().execute()
    
    total_bruto = qtd * valor_venda
    # 2. Cálculo Fiscal
    imposto = total_bruto * (regra.data['aliquota_icms'] + regra.data['aliquota_iss'])
    valor_liquido = total_bruto - imposto
    
    # 3. Lançamento Contábil Automático (Partida Dobrada)
    supabase.table("lancamentos").insert([
        {"natureza": "Receita", "descricao": f"VENDA {prod.data['nome']}", "tipo": "Crédito", "valor": valor_liquido, "status": "Pago"},
        {"natureza": "Passivo Circulante", "descricao": f"IMPOSTO {prod.data['nome']}", "tipo": "Crédito", "valor": imposto, "status": "Pendente"}
    ]).execute()
    
    # 4. Baixa de Estoque (WMS)
    supabase.table("produtos").update({"saldo_estoque": prod.data['saldo_estoque'] - qtd}).eq("id", produto_id).execute()
