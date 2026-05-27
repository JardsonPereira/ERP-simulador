import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import get_data_cached, check_auth, inject_css

check_auth()
inject_css()

st.header("💵 Fluxo de Caixa")

user_id = st.session_state.user.id
lancamentos = get_data_cached("lancamentos", user_id)
contas = get_data_cached("contas", user_id)

if lancamentos and contas:
    df = pd.DataFrame(lancamentos).merge(pd.DataFrame(contas), left_on='conta_id', right_on='id')
    
    # 1. Limpeza forçada dos dados
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # 2. PADRONIZAÇÃO AGRESSIVA: 
    # O .strip() remove espaços ocultos e o .capitalize() trata maiúsculas/minúsculas
    df['status_padronizado'] = df['status_financeiro'].astype(str).str.strip().str.capitalize()

    # --- DIAGNÓSTICO IMPORTANTE ---
    # Isso vai listar na tela todos os nomes de status que o seu código está enxergando.
    # Verifique se aparece "Saída" exatamente como você espera.
    st.write("Status encontrados no banco:", df['status_padronizado'].unique())

    # 3. Lógica de cálculo com sinais matemáticos
    def calcular_efetivo(row):
        status = row['status_padronizado']
        valor = row['valor']
        
        # AQUI É O PONTO CHAVE: 
        # Se o seu diagnóstico mostrar algo diferente de 'Saída', 
        # basta adicionar o nome correto aqui com 'or'.
        if status == 'Entrada':
            return valor
        elif status == 'Saída':
            return -abs(valor)
        return 0

    df['valor_efetivo'] = df.apply(calcular_efetivo, axis=1)

    # 4. Filtros e Exibição
    d_inicio = st.date_input("Início", value=df['data_lancamento'].min().date())
    d_fim = st.date_input("Fim", value=df['data_lancamento'].max().date())
    
    df_fc = df[(df['data_lancamento'].dt.date >= d_inicio) & (df['data_lancamento'].dt.date <= d_fim)].copy()
    
    saldo_final = df_fc['valor_efetivo'].sum()
    st.metric("Saldo Final do Período", f"R$ {saldo_final:,.2f}")
    
    st.dataframe(df_fc[['status_padronizado', 'valor', 'valor_efetivo']])

else:
    st.info("Nenhum dado encontrado.")
