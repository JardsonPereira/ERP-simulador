import streamlit as st
import sys
import os
from datetime import date

# --- CORREÇÃO DO IMPORT ---
# Adiciona a pasta raiz (onde está o utils.py) ao caminho de busca do Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Agora podemos importar normalmente do nosso arquivo utils.py
from utils import get_supabase, check_auth, show_auth_sidebar

# --- INICIALIZAÇÃO E AUTENTICAÇÃO ---
# 1. Checa a autenticação (se não estiver logado, a função já manda de volta pro app.py)
user = check_auth()

# 2. Inicializa o cliente do Supabase
supabase = get_supabase()

# 3. Exibe a sidebar com o usuário logado e o botão de deslogar
show_auth_sidebar(supabase)

# Extrai o ID do usuário de forma segura (lidando com dict ou objeto)
user_id = getattr(user, 'id', None) or (user.get('id') if isinstance(user, dict) else None)

# --- INTERFACE PRINCIPAL ---
st.title("💰 Lançamentos Financeiros")

# --- FORMULÁRIO DE INSERÇÃO ---
with st.form("lancamento_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        data_lancamento = st.date_input("Data", date.today())
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
    with col2:
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        descricao = st.text_input("Descrição")
    
    submit = st.form_submit_button("Salvar Lançamento")

    if submit:
        if not descricao:
            st.warning("A descrição é obrigatória!")
        elif not user_id:
            st.error("Erro ao identificar o usuário. Por favor, faça login novamente.")
        else:
            dados = {
                "user_id": user_id,
                "data": str(data_lancamento),
                "descricao": descricao,
                # Salva despesas como negativo para facilitar os cálculos de saldo futuro
                "valor": valor if tipo == "Receita" else -valor,
                "tipo": tipo
            }
            try:
                # Envia para a tabela 'lancamentos' no Supabase
                supabase.table("lancamentos").insert(dados).execute()
                st.success("Lançamento salvo com sucesso!")
                st.rerun() # Atualiza a página automaticamente para exibir o novo dado
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

# --- LISTAGEM (HISTÓRICO) ---
st.subheader("Histórico de Lançamentos")

if user_id:
    try:
        # Busca os lançamentos filtrando pelo usuário atual e ordenando pela data mais recente
        response = supabase.table("lancamentos").select("*").eq("user_id", user_id).order("data", desc=True).execute()
        
        if response.data:
            # st.dataframe é melhor que st.table pois permite ordenação nativa pelo usuário
            st.dataframe(response.data, use_container_width=True)
        else:
            st.info("Nenhum lançamento encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
