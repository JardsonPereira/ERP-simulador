import pandas as pd

def registrar_lancamento(supabase, user_id, desc, nat, tipo, valor, justificativa, status, data):
    # A lógica de Fluxo de Caixa depende do status ser 'Entrada' ou 'Pago'
    # O lançamento contábil puro (Razonetes) ocorre sempre.
    payload = {
        "user_id": user_id,
        "descricao": desc,
        "natureza": nat,
        "tipo": tipo,
        "valor": valor,
        "justificativa": justificativa,
        "status": status,
        "data_lancamento": str(data)
    }
    supabase.table("lancamentos").insert(payload).execute()
