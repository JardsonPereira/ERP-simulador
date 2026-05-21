def registrar_lancamento(supabase, user_id, descricao, natureza, tipo, valor, justificativa, status):
    payload = {
        "user_id": user_id,
        "descricao": descricao,
        "natureza": natureza,
        "tipo": tipo,
        "valor": valor,
        "justificativa": justificativa,
        "status": status,
        "data_lancamento": str(pd.Timestamp.now().date())
    }
    supabase.table("lancamentos").insert(payload).execute()

def processar_venda_integrada(supabase, user_id, produto_id, qtd, valor_venda):
    # Lógica de integração (Fiscal + Estoque + Contábil)
    prod = supabase.table("produtos").select("*").eq("id", produto_id).single().execute()
    regra = supabase.table("config_tributaria").select("*").eq("categoria", prod.data['categoria']).single().execute()
    
    total_bruto = qtd * valor_venda
    imposto = total_bruto * (regra.data['aliquota_icms'] + regra.data['aliquota_iss'])
    
    # Lançamentos integrados
    registrar_lancamento(supabase, user_id, f"VENDA {prod.data['nome']}", "Receita", "Crédito", total_bruto - imposto, "Venda Integrada", "Entrada")
    registrar_lancamento(supabase, user_id, f"IMPOSTO {prod.data['nome']}", "Passivo Circulante", "Crédito", imposto, "Imposto Integrado", "Pendente")
    
    # Baixa estoque
    supabase.table("produtos").update({"saldo_estoque": prod.data['saldo_estoque'] - qtd}).eq("id", produto_id).execute()
