import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="ContabilApp - Sistema Integrado", layout="wide")

# --- CONFIGURAÇÃO DE ADMINISTRAÇÃO ---
EMAIL_ADMIN = "jardsonspereira81@gmail.com"

# --- ESTADOS DO SISTEMA ---
if 'user' not in st.session_state: st.session_state.user = None
if 'edit_id' not in st.session_state: st.session_state.edit_id = None
if 'form_count' not in st.session_state: st.session_state.form_count = 0
if 'menu_opcao' not in st.session_state: st.session_state.menu_opcao = "📊 Razonetes"
if 'tem_perfil' not in st.session_state: st.session_state.tem_perfil = False

# Inicialização do filtro persistente no session_state
if 'filtro_admin' not in st.session_state:
    if st.session_state.user and st.session_state.user.email == EMAIL_ADMIN:
        st.session_state.filtro_admin = "Todos"
    elif st.session_state.user:
        st.session_state.filtro_admin = st.session_state.user.id
    else:
        st.session_state.filtro_admin = "Todos"

id_usuario_filtrado = st.session_state.filtro_admin

try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception:
    st.error("Erro de conexão. Verifique as Secrets no Streamlit Cloud.")
    st.stop()

# --- FUNÇÕES DE CÁLCULO CONTÁBIL ---
def is_admin():
    """Verifica se o usuário atualmente logado é o administrador"""
    if st.session_state.user and hasattr(st.session_state.user, 'email'):
        return st.session_state.user.email == EMAIL_ADMIN
    return False

def get_saldo_total_por_natureza(df, nat):
    """Calcula o saldo acumulado de um grupo contábil específico de forma segura"""
    if df is None or df.empty or 'natureza' not in df.columns or 'tipo' not in df.columns: 
        return 0.0
    d = df[(df['natureza'] == nat) & (df['tipo'] == 'Débito')]['valor'].sum()
    c = df[(df['natureza'] == nat) & (df['tipo'] == 'Crédito')]['valor'].sum()
    if 'Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']:
        return float(d - c)
    return float(c - d)

def agrupar_por_conta(df):
    if df is None or df.empty: return []
    linhas = []
    for conta in sorted(df['descricao'].unique()):
        sub = df[df['descricao'] == conta]
        d = sub[sub['tipo'] == 'Débito']['valor'].sum()
        c = sub[sub['tipo'] == 'Crédito']['valor'].sum()
        nat = sub['natureza'].iloc[0]
        
        if 'Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']:
            saldo = d - c
        else:
            saldo = c - d
        linhas.append((conta.title(), abs(saldo)))
    return linhas

def total_grupo_com_sinal(df, nat):
    if df is None or df.empty: return 0.0
    d = df[df['tipo'] == 'Débito']['valor'].sum()
    c = df[df['tipo'] == 'Crédito']['valor'].sum()
    if 'Ativo' in nat or nat in ['Despesa', 'Encargos Financeiros']:
        return d - c
    return c - d

def verificar_perfil(u_id):
    try:
        res = supabase.table("perfis").select("nome_usuario").eq("id", u_id).execute()
        if res.data:
            st.session_state.tem_perfil = True
            return True
        st.session_state.tem_perfil = False
        return False
    except Exception:
        return False

def obter_todos_usuarios_mapeados():
    mapeamento = {"Todos os Usuários": "Todos"}
    if st.session_state.user:
        mapeamento[f"Meu Usuário (Admin)"] = st.session_state.user.id
    try:
        res_perfis = supabase.table("perfis").select("id, nome_usuario").execute()
        df_perfis = pd.DataFrame(res_perfis.data)
        res_lanc = supabase.table("lancamentos").select("user_id").execute()
        df_lanc = pd.DataFrame(res_lanc.data)
        perfis_dict = {}
        if not df_perfis.empty and 'id' in df_perfis.columns and 'nome_usuario' in df_perfis.columns:
            perfis_dict = dict(zip(df_perfis['id'], df_perfis['nome_usuario']))
        if not df_lanc.empty and 'user_id' in df_lanc.columns:
            ids_unicos = df_lanc['user_id'].unique().tolist()
            for uid in ids_unicos:
                if uid == st.session_state.user.id: continue  
                if uid in perfis_dict:
                    mapeamento[perfis_dict[uid]] = uid
                else:
                    mapeamento[f"Sem Nome ({uid[:8]}...)"] = uid
        return mapeamento
    except Exception:
        return mapeamento

def carregar_dados(u_id, usuario_selecionado="Todos"):
    try:
        if is_admin() and usuario_selecionado == "Todos":
            res = supabase.table("lancamentos").select("*").execute()
        elif is_admin() and usuario_selecionado != "Todos":
            res = supabase.table("lancamentos").select("*").eq("user_id", usuario_selecionado).execute()
        else:
            res = supabase.table("lancamentos").select("*").eq("user_id", u_id).execute()
            
        temp_df = pd.DataFrame(res.data)
        if not temp_df.empty:
            temp_df['data_lancamento'] = pd.to_datetime(temp_df['data_lancamento']).dt.date
            if 'status' not in temp_df.columns: temp_df['status'] = 'Pago'
            if 'justificativa' not in temp_df.columns: temp_df['justificativa'] = ''
            temp_df['natureza'] = temp_df['natureza'].replace({'Ativo': 'Ativo Circulante', 'Passivo': 'Passivo Circulante'})
            return temp_df
        else:
            return pd.DataFrame(columns=['descricao', 'natureza', 'tipo', 'valor', 'justificativa', 'status', 'data_lancamento', 'user_id'])
    except Exception: 
        return pd.DataFrame(columns=['descricao', 'natureza', 'tipo', 'valor', 'justificativa', 'status', 'data_lancamento', 'user_id'])

def obter_contas_do_usuario(u_id, usuario_selecionado):
    try:
        alvo = u_id if usuario_selecionado == "Todos" else usuario_selecionado
        res = supabase.table("lancamentos").select("descricao").eq("user_id", alvo).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            return sorted(df['descricao'].dropna().unique().tolist())
        return []
    except:
        return []

def gerar_pdf(user_email, df_per, data_i, data_f, s_ini, s_fin, v_at, v_pas, v_pl, v_rec_total, v_desp_total, v_ebitda, v_finan_total, v_lucro):
    pdf = FPDF()
    pdf.add_page()
    def clean_str(s): return str(s).encode('latin-1', 'ignore').decode('latin-1')
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 8, clean_str("RELATÓRIO CONTÁBIL CONSOLIDADO"), ln=True, align="C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(190, 5, clean_str(f"Usuário: {user_email}"), ln=True, align="C")
    pdf.cell(190, 5, clean_str(f"Período: {data_i.strftime('%d/%m/%Y')} até {data_f.strftime('%d/%m/%Y')}"), ln=True, align="C")
    pdf.ln(5)

    # 1. FLUXO DE CAIXA
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 7, clean_str("1. FLUXO DE CAIXA E VARIAÇÃO"), ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(63, 7, clean_str(f"Saldo Inicial: R$ {s_ini:,.2f}"), border=1)
    pdf.cell(63, 7, clean_str(f"Saldo Final: R$ {s_fin:,.2f}"), border=1)
    pdf.cell(64, 7, clean_str(f"Variação Líquida: R$ {s_fin - s_ini:,.2f}"), border=1, ln=True)
    pdf.ln(4)

    # 2. DRE DETALHADA NO PDF
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 7, clean_str("2. DEMONSTRAÇÃO DO RESULTADO (DRE DETALHADA)"), ln=True)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(140, 6, clean_str("(+) RECEITAS"), border=1)
    pdf.cell(50, 6, clean_str(f"R$ {v_rec_total:,.2f}"), border=1, ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    df_rec = df_per[df_per['natureza'] == 'Receita'] if not df_per.empty else pd.DataFrame()
    for conta, valor in agrupar_por_conta(df_rec):
        pdf.cell(140, 5.5, clean_str(f"   {conta}"), border=1)
        pdf.cell(50, 5.5, clean_str(f"R$ {valor:,.2f}"), border=1, ln=True, align="R")
        
    pdf.set_font("Arial", "B", 9)
    pdf.cell(140, 6, clean_str("(-) DESPESAS OPERACIONAIS"), border=1)
    pdf.cell(50, 6, clean_str(f"R$ ({v_desp_total:,.2f})"), border=1, ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    df_desp = df_per[df_per['natureza'] == 'Despesa'] if not df_per.empty else pd.DataFrame()
    for conta, valor in agrupar_por_conta(df_desp):
        pdf.cell(140, 5.5, clean_str(f"   {conta}"), border=1)
        pdf.cell(50, 5.5, clean_str(f"R$ ({valor:,.2f})"), border=1, ln=True, align="R")
        
    pdf.set_font("Arial", "B", 9)
    pdf.cell(140, 6, clean_str("(=) EBITDA"), border=1)
    pdf.cell(50, 6, clean_str(f"R$ {v_ebitda:,.2f}"), border=1, ln=True, align="R")
    pdf.cell(140, 6, clean_str("(-) ENCARGOS FINANCEIROS / IMPOSTOS"), border=1)
    pdf.cell(50, 6, clean_str(f"R$ ({v_finan_total:,.2f})"), border=1, ln=True, align="R")
    pdf.set_font("Arial", "", 9)
    df_fin = df_per[df_per['natureza'] == 'Encargos Financeiros'] if not df_per.empty else pd.DataFrame()
    for conta, valor in agrupar_por_conta(df_fin):
        pdf.cell(140, 5.5, clean_str(f"   {conta}"), border=1)
        pdf.cell(50, 5.5, clean_str(f"R$ ({valor:,.2f})"), border=1, ln=True, align="R")
        
    pdf.set_font("Arial", "B", 9)
    label_resultado = "(=) LUCRO LÍQUIDO DO PERÍODO" if v_lucro >= 0 else "(=) PREJUÍZO LÍQUIDO DO PERÍODO"
    pdf.cell(140, 7, clean_str(label_resultado), border=1)
    pdf.cell(50, 7, clean_str(f"R$ {v_lucro:,.2f}"), border=1, ln=True, align="R")
    pdf.ln(4)

    # 3. BALANÇO PATRIMONIAL CONSOLIDADO
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 7, clean_str("3. BALANÇO PATRIMONIAL CONSOLIDADO"), ln=True)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(65, 7, clean_str("ATIVO"), border=1, align="C")
    pdf.cell(30, 7, clean_str("Valor (R$)"), border=1, align="R")
    pdf.cell(65, 7, clean_str("PASSIVO E PL"), border=1, align="C")
    pdf.cell(30, 7, clean_str("Valor (R$)"), border=1, align="R")
    pdf.ln()

    df_at_circ = df_per[df_per['natureza'] == 'Ativo Circulante'] if not df_per.empty else pd.DataFrame()
    df_at_nc = df_per[df_per['natureza'] == 'Ativo Não Circulante'] if not df_per.empty else pd.DataFrame()
    df_pass_circ = df_per[df_per['natureza'] == 'Passivo Circulante'] if not df_per.empty else pd.DataFrame()
    df_pass_nc = df_per[df_per['natureza'] == 'Passivo Não Circulante'] if not df_per.empty else pd.DataFrame()
    filt_pl = df_per[df_per['natureza'] == 'Patrimônio Líquido'] if not df_per.empty else pd.DataFrame()
    
    linhas_ativo = []
    linhas_passivo_pl = []

    v_at_circ = total_grupo_com_sinal(df_at_circ, 'Ativo Circulante')
    linhas_ativo.append(("ATIVO CIRCULANTE", v_at_circ, True))
    for c, v in agrupar_por_conta(df_at_circ): linhas_ativo.append((f"  {c}", v, False))
    v_at_nc = total_grupo_com_sinal(df_at_nc, 'Ativo Não Circulante')
    linhas_ativo.append(("ATIVO NÃO CIRCULANTE", v_at_nc, True))
    for c, v in agrupar_por_conta(df_at_nc): linhas_ativo.append((f"  {c}", v, False))

    v_pass_circ = total_grupo_com_sinal(df_pass_circ, 'Passivo Circulante')
    linhas_passivo_pl.append(("PASSIVO CIRCULANTE", v_pass_circ, True))
    for c, v in agrupar_por_conta(df_pass_circ): linhas_passivo_pl.append((f"  {c}", v, False))
    v_pass_nc = total_grupo_com_sinal(df_pass_nc, 'Passivo Não Circulante')
    linhas_passivo_pl.append(("PASSIVO NÃO CONVERTIDO / LONGO PRAZO", v_pass_nc, True))
    for c, v in agrupar_por_conta(df_pass_nc): linhas_passivo_pl.append((f"  {c}", v, False))
    
    linhas_passivo_pl.append(("", None, False))
    linhas_passivo_pl.append(("PATRIMÔNIO LÍQUIDO", None, True))
    for c, v in agrupar_por_conta(filt_pl): linhas_passivo_pl.append((f"  {c}", v, False))
    linhas_passivo_pl.append(("  Lucros/Prejuízos Acumulados", v_lucro, False))

    max_linhas = max(len(linhas_ativo), len(linhas_passivo_pl))
    pdf.set_font("Arial", "", 8)
    for index in range(max_linhas):
        if index < len(linhas_ativo):
            desc_at, val_at, is_bold_at = linhas_ativo[index]
            pdf.set_font("Arial", "B" if is_bold_at else "", 8)
            pdf.cell(65, 5.5, clean_str(desc_at), border=1)
            pdf.cell(30, 5.5, f"{val_at:,.2f}" if val_at is not None else "", border=1, align="R")
        else:
            pdf.cell(65, 5.5, "", border=1)
            pdf.cell(30, 5.5, "", border=1)

        if index < len(linhas_passivo_pl):
            desc_pas, val_pas, is_bold_pas = linhas_passivo_pl[index]
            pdf.set_font("Arial", "B" if is_bold_pas else "", 8)
            pdf.cell(65, 5.5, clean_str(desc_pas), border=1)
            pdf.cell(30, 5.5, f"{val_pas:,.2f}" if val_pas is not None else "", border=1, align="R")
        else:
            pdf.cell(65, 5.5, "", border=1)
            pdf.cell(30, 5.5, "", border=1)
        pdf.ln()

    pdf.set_font("Arial", "B", 9)
    pdf.cell(65, 6.5, clean_str("TOTAL DO ATIVO"), border=1)
    pdf.cell(30, 6.5, f"{v_at:,.2f}", border=1, align="R")
    pdf.cell(65, 6.5, clean_str("TOTAL DO PASSIVO + PL"), border=1)
    pdf.cell(30, 6.5, f"{v_pas + v_pl + v_lucro:,.2f}", border=1, align="R")
    pdf.ln(8)

    # 4. LANÇAMENTOS DO PERÍODO
    pdf.set_font("Arial", "B", 11)
    pdf.cell(190, 7, clean_str("4. LANÇAMENTOS DO PERÍODO"), ln=True)
    pdf.set_font("Arial", "B", 8.5)
    pdf.cell(20, 6.5, "Data", border=1, align="C")
    pdf.cell(50, 6.5, "Conta", border=1)
    pdf.cell(30, 6.5, "Grupo", border=1)
    pdf.cell(20, 6.5, "Operação", border=1, align="C")
    pdf.cell(25, 6.5, "Valor", border=1, align="R")
    pdf.cell(45, 6.5, "Status/Justificativa", border=1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    if not df_per.empty:
        for _, r in df_per.sort_values('data_lancamento').iterrows():
            pdf.cell(20, 5.5, str(r['data_lancamento']), border=1, align="C")
            pdf.cell(50, 5.5, clean_str(r['descricao'][:25]), border=1)
            pdf.cell(30, 5.5, clean_str(r['natureza'][:15]), border=1) 
            pdf.cell(20, 5.5, clean_str(r['tipo']), border=1, align="C")
            pdf.cell(25, 5.5, f"R$ {r['valor']:,.2f}", border=1, align="R")
            pdf.cell(45, 5.5, clean_str(r['justificativa'][:25] if r['justificativa'] else r['status']), border=1)
            pdf.ln()
    else:
        pdf.cell(190, 6, clean_str("Nenhum lançamento encontrado no período."), border=1, align="C", ln=True)
    return pdf.output()

# --- AUTENTICAÇÃO ---
if st.session_state.user is None:
    st.sidebar.title("🔐 Acesso")
    menu = st.sidebar.radio("Escolha", ["Login", "Criar Conta"])
    email = st.sidebar.text_input("E-mail").lower().strip()
    senha = st.sidebar.text_input("Senha", type="password")
    if menu == "Login" and st.sidebar.button("Entrar"):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
            st.session_state.user = res.user
            st.rerun()
        except: st.sidebar.error("E-mail ou senha incorretos.")
    elif menu == "Criar Conta" and st.sidebar.button("Cadastrar"):
        try:
            supabase.auth.sign_up({"email": email, "password": senha})
            st.sidebar.success("Conta criada! Faça o login agora.")
        except Exception as e: st.sidebar.error(f"Erro ao cadastrar: {e}")
    st.stop()

# --- BLINDAGEM DE CADASTRO OBRIGATÓRIO DE PERFIL ---
if not verificar_perfil(st.session_state.user.id):
    st.title("📋 Complete o seu Cadastro")
    st.write("Para continuar acessando o sistema, insira o seu nome ou o nome da sua empresa para identificação.")
    with st.form("form_completar_cadastro"):
        nome_input = st.text_input("Nome Corporativo / Usuário").upper().strip()
        if st.form_submit_button("Salvar e Acessar"):
            if len(nome_input) < 3: st.error("Insira um nome de no mínimo 3 caracteres.")
            else:
                try:
                    supabase.table("perfis").insert({"id": st.session_state.user.id, "nome_usuario": nome_input}).execute()
                    st.session_state.tem_perfil = True
                    st.success("Perfil configurado!")
                    st.rerun()
                except Exception as e: st.error(f"Erro ao salvar: {e}")
    st.stop()

# --- INTERFACE PRINCIPAL E BARRA LATERAL ---
with st.sidebar:
    st.write(f"👤 **{st.session_state.user.email}**")
    if is_admin(): st.write("⭐ **Modo Administrador Ativo**")
    if st.button("Sair"):
        st.session_state.user = None
        st.session_state.tem_perfil = False
        if 'filtro_admin' in st.session_state: del st.session_state.filtro_admin
        st.rerun()
    st.sidebar.divider()
    
    if is_admin():
        st.header("🔍 Painel Admin")
        dict_usuarios = obter_todos_usuarios_mapeados()
        lista_nomes_usuarios = list(dict_usuarios.keys())
        lista_ids_usuarios = list(dict_usuarios.values())
        idx_atual_filtro = lista_ids_usuarios.index(st.session_state.filtro_admin) if st.session_state.filtro_admin in lista_ids_usuarios else 0
        nome_selecionado = st.selectbox("Filtrar lançamentos de:", lista_nomes_usuarios, index=idx_atual_filtro)
        st.session_state.filtro_admin = dict_usuarios[nome_selecionado]
        id_usuario_filtrado = st.session_state.filtro_admin
        st.sidebar.divider()
    
    contas_existentes = obter_contas_do_usuario(st.session_state.user.id, id_usuario_filtrado)
    
    if st.session_state.edit_id:
        st.header("📝 Editar Lançamento")
        df_edicao = carregar_dados(st.session_state.user.id, id_usuario_filtrado)
        linhas_para_editar = df_edicao[df_edicao['id'] == st.session_state.edit_id] if not df_edicao.empty else pd.DataFrame()
        reg = linhas_para_editar.iloc[0] if not linhas_para_editar.empty else {"descricao": "", "natureza": "Ativo Circulante", "tipo": "Débito", "valor": 0.0, "justificativa": "", "status": "Pago", "data_lancamento": datetime.now().date()}
        if st.button("Cancelar Edição"):
            st.session_state.edit_id = None
            st.rerun()
    else:
        st.header("➕ Novo Lançamento")
        reg = {"descricao": "", "natureza": "Ativo Circulante", "tipo": "Débito", "valor": 0.0, "justificativa": "", "status": "Pago", "data_lancamento": datetime.now().date()}

    # ESTRUTURA BLINDADA DO FORMULÁRIO CONTRA CONFLITOS DE INSTANCIAÇÃO
    with st.form(key=f"form_sidebar_{id_usuario_filtrado}_{st.session_state.form_count}"):
        
        # Correção Definitiva do Fluxo: Seletor explícito de ação elimina o sumiço do input de texto
        tipo_conta_acao = st.radio("Método da Conta", ["Conta Existente", "+ Criar Nova Conta"], horizontal=True)
        
        if tipo_conta_acao == "Conta Existente" and contas_existentes:
            conta_sel = st.selectbox("Selecione a Conta", contas_existentes)
            desc_input = conta_sel
        else:
            desc_input = st.text_input("Nome da Nova Conta (Digite)", key="txt_nova_conta_estatico").upper().strip()
            conta_sel = "+ Adicionar Nova Conta"
            
        data_f = st.date_input("Data", value=reg['data_lancamento'])
        grupos = ["Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido", "Receita", "Despesa", "Encargos Financeiros"]
        
        idx_inicial_grupo = grupos.index(reg['natureza']) if reg['natureza'] in grupos else 0
        if tipo_conta_acao == "+ Criar Nova Conta" and desc_input:
            if "RECEBER" in desc_input or "CLIENTE" in desc_input: idx_inicial_grupo = grupos.index("Ativo Circulante")
            elif "VEICULO" in desc_input or "IMOBILIZADO" in desc_input: idx_inicial_grupo = grupos.index("Ativo Não Circulante")

        nat = st.selectbox("Grupo (Classificação Contábil)", grupos, index=idx_inicial_grupo)
        tipo = st.radio("Operação", ["Débito", "Crédito"], index=0 if reg['tipo'] == "Débito" else 1, horizontal=True)
        valor = st.number_input("Valor", min_value=0.0, value=float(reg['valor']))
        opcoes_status = ["Pago", "Entrada", "Pendente", "Investimento", "Transferência Interna"]
        status_pag = st.selectbox("Status", opcoes_status, index=opcoes_status.index(reg['status']) if reg['status'] in opcoes_status else 0)
        just_input = st.text_area("Justificativa", value=reg['justificativa'])
        
        is_disabled = is_admin() and id_usuario_filtrado == "Todos" and not st.session_state.edit_id
        if is_disabled: st.warning("⚠️ Selecione um usuário ou 'Meu Usuário (Admin)' acima para salvar.")
            
        if st.form_submit_button("Confirmar", disabled=is_disabled):
            if not desc_input:
                st.error("Por favor, preencha o nome da conta.")
            else:
                user_dono = id_usuario_filtrado if id_usuario_filtrado != "Todos" else st.session_state.user.id
                payload = {"user_id": user_dono, "descricao": desc_input, "natureza": nat, "tipo": tipo, "valor": valor, "justificativa": just_input, "status": status_pag, "data_lancamento": str(data_f)}
                if st.session_state.edit_id: supabase.table("lancamentos").update(payload).eq("id", st.session_state.edit_id).execute()
                else: supabase.table("lancamentos").insert(payload).execute()
                st.session_state.edit_id = None
                st.session_state.form_count += 1
                st.rerun()

# --- CARREGAMENTO OFICIAL E RENDERIZAÇÃO DA TELA ---
df_base = carregar_dados(st.session_state.user.id, id_usuario_filtrado)

def get_caixa_acumulado(data_limite):
    if df_base.empty: return 0.0
    sub = df_base[df_base['data_lancamento'] <= data_limite]
    if 'status' in sub.columns and 'valor' in sub.columns:
        return sub[sub['status'] == "Entrada"]['valor'].sum() - sub[sub['status'] == "Pago"]['valor'].sum()
    return 0.0

st.markdown("""<style>
    .conta-card { background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #e2e8f0; }
    .conta-titulo { background: #1e293b; color: white; padding: 10px; text-align: center; font-weight: 700; border-radius: 12px 12px 0 0; }
    .conta-rodape { padding: 8px; background: #f8fafc; text-align: center; font-weight: 700; border-top: 1px solid #e2e8f0; border-radius: 0 0 12px 12px; }
    .valor-deb { color: #059669; font-size: 0.8rem; padding: 2px 10px; font-weight: 600; }
    .valor-cre { color: #dc2626; font-size: 0.8rem; text-align: right; padding: 2px 10px; font-weight: 600; }
    .just-box { font-size: 0.65rem; color: #64748b; font-style: italic; padding: 0 10px 5px 10px; line-height: 1.1; }
    .dre-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.95rem; }
    .dre-subrow { display: flex; justify-content: space-between; padding: 3px 0 3px 20px; border-bottom: 1px solid #f8fafc; font-size: 0.85rem; color: #475569; font-style: italic; }
    .dre-total { font-weight: bold; border-top: 2px solid #1e293b; margin-top: 10px; padding-top: 5px; font-size: 1.1rem; }
</style>""", unsafe_allow_html=True)

col_nav = st.columns(5)
opcoes_menu = ["📊 Razonetes", "🧾 Balancete", "📈 DRE", "💸 Fluxo de Caixa", "⚙️ Gestão"]
for i, op in enumerate(opcoes_menu):
    if col_nav[i].button(op, use_container_width=True): st.session_state.menu_opcao = op

st.divider()

f1, f2 = st.columns(2)
with f1: data_ini = st.date_input("Início do Período", value=datetime.now().date().replace(day=1))
with f2: data_fim = st.date_input("Fim do Período", value=datetime.now().date())
df_periodo = df_base[(df_base['data_lancamento'] >= data_ini) & (df_base['data_lancamento'] <= data_fim)].copy()

s_ini = get_caixa_acumulado(data_ini - timedelta(days=1))
s_fin = get_caixa_acumulado(data_fim)

v_rec = df_periodo[(df_periodo['natureza'] == 'Receita') & (df_periodo['tipo'] == 'Crédito')]['valor'].sum() if not df_periodo.empty else 0.0
v_desp_op = df_periodo[(df_periodo['natureza'] == 'Despesa') & (df_periodo['tipo'] == 'Débito')]['valor'].sum() if not df_periodo.empty else 0.0
v_finan = df_periodo[(df_periodo['natureza'] == 'Encargos Financeiros') & (df_periodo['tipo'] == 'Débito')]['valor'].sum() if not df_periodo.empty else 0.0
v_lucro = v_rec - v_desp_op - v_finan

v_at_total = get_saldo_total_por_natureza(df_periodo, 'Ativo Circulante') + get_saldo_total_por_natureza(df_periodo, 'Ativo Não Circulante')
v_pas_total = get_saldo_total_por_natureza(df_periodo, 'Passivo Circulante') + get_saldo_total_por_natureza(df_periodo, 'Passivo Não Circulante')
v_pl_per = get_saldo_total_por_natureza(df_periodo, 'Patrimônio Líquido')

col_imp, _ = st.columns([1, 4])
with col_imp:
    pdf_bytes = gerar_pdf(st.session_state.user.email, df_periodo, data_ini, data_fim, s_ini, s_fin, v_at_total, v_pas_total, v_pl_per, v_rec, v_desp_op, v_rec - v_desp_op, v_finan, v_lucro)
    st.download_button("🖨️ Baixar PDF", data=bytes(pdf_bytes), file_name=f"Relatorio_{data_ini}.pdf", mime="application/pdf")

if df_periodo.empty and st.session_state.menu_opcao != "⚙️ Gestão":
    st.info("Sem dados cadastrados neste período.")
else:
    if st.session_state.menu_opcao == "📊 Razonetes":
        for grupo in ["Ativo Circulante", "Ativo Não Circulante", "Passivo Circulante", "Passivo Não Circulante", "Patrimônio Líquido", "Receita", "Despesa", "Encargos Financeiros"]:
            df_g = df_periodo[df_periodo['natureza'] == grupo] if not df_periodo.empty else pd.DataFrame()
            if not df_g.empty:
                st.subheader(grupo)
                cols = st.columns(3)
                for i, conta in enumerate(sorted(df_g['descricao'].unique())):
                    df_c = df_g[df_g['descricao'] == conta]
                    v_d, v_c = df_c[df_c['tipo']=='Débito']['valor'].sum(), df_c[df_c['tipo']=='Crédito']['valor'].sum()
                    saldo = (v_d - v_c) if ('Ativo' in grupo or grupo in ["Despesa", "Encargos Financeiros"]) else (v_c - v_d)
                    with cols[i % 3]:
                        st.markdown(f'<div class="conta-card"><div class="conta-titulo">{conta}</div>', unsafe_allow_html=True)
                        c1, c2 = st.columns(2)
                        with c1: 
                            for _, r in df_c[df_c['tipo']=='Débito'].iterrows(): st.markdown(f'<div class="valor-deb">D: {r["valor"]:,.2f}</div><div class="just-box">{r["justificativa"]}</div>', unsafe_allow_html=True)
                        with c2: 
                            for _, r in df_c[df_c['tipo']=='Crédito'].iterrows(): st.markdown(f'<div class="valor-cre">C: {r["valor"]:,.2f}</div><div class="just-box">{r["justificativa"]}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="conta-rodape">Saldo: R$ {saldo:,.2f}</div></div>', unsafe_allow_html=True)

    elif st.session_state.menu_opcao == "🧾 Balancete":
        bal_data = []
        for conta in sorted(df_periodo['descricao'].unique()):
            df_c = df_periodo[df_periodo['descricao'] == conta]
            d, c = df_c[df_c['tipo']=='Débito']['valor'].sum(), df_c[df_c['tipo']=='Crédito']['valor'].sum()
            bal_data.append({"Conta": conta, "Grupo": df_c['natureza'].iloc[0], "Débito": d, "Crédito": c, "SD": d-c if d>c else 0, "SC": c-d if c>d else 0})
        df_bal = pd.DataFrame(bal_data) if bal_data else pd.DataFrame(columns=["Conta", "Grupo", "Débito", "Crédito", "SD", "SC"])
        st.table(df_bal.style.format(formatter={"Débito": "R$ {:,.2f}", "Crédito": "R$ {:,.2f}", "SD": "R$ {:,.2f}", "SC": "R$ {:,.2f}"}))

    elif st.session_state.menu_opcao == "📈 DRE":
        col_d, _ = st.columns([2, 1])
        with col_d:
            st.markdown(f'<div class="dre-row" style="font-weight: bold;"><span>(+) RECEITAS</span><span>R$ {v_rec:,.2f}</span></div>', unsafe_allow_html=True)
            for conta, valor in agrupar_por_conta(df_periodo[df_periodo['natureza'] == 'Receita']):
                st.markdown(f'<div class="dre-subrow"><span>{conta}</span><span>R$ {valor:,.2f}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="dre-row" style="font-weight: bold; margin-top: 10px;"><span>(-) DESPESAS OPERACIONAIS</span><span>(R$ {v_desp_op:,.2f})</span></div>', unsafe_allow_html=True)
            for conta, valor in agrupar_por_conta(df_periodo[df_periodo['natureza'] == 'Despesa']):
                st.markdown(f'<div class="dre-subrow"><span>{conta}</span><span>(R$ {valor:,.2f})</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="dre-total">(=) EBITDA: R$ {v_rec - v_desp_op:,.2f}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="dre-total" style="color:{"#059669" if v_lucro >= 0 else "#dc2626"};">(=) LUCRO LÍQUIDO: R$ {v_lucro:,.2f}</div>', unsafe_allow_html=True)

    elif st.session_state.menu_opcao == "💸 Fluxo de Caixa":
        st.metric("Saldo Líquido Disponível em Caixa", f"R$ {s_fin:,.2f}")
        st.dataframe(df_periodo[['data_lancamento', 'descricao', 'valor', 'tipo', 'status']], use_container_width=True, hide_index=True)

    elif st.session_state.menu_opcao == "⚙️ Gestão":
        if not df_base.empty:
            for _, row in df_base.sort_values('data_lancamento', ascending=False).iterrows():
                with st.expander(f"{row['data_lancamento']} | {row['descricao']} | R$ {row['valor']:,.2f}"):
                    c1, c2 = st.columns(2)
                    if c1.button("✏️ Editar", key=f"ed_{row['id']}"):
                        st.session_state.edit_id = row['id']
                        st.rerun()
                    if c2.button("🗑️ Excluir", key=f"ex_{row['id']}"):
                        supabase.table("lancamentos").delete().eq("id", row['id']).execute()
                        st.rerun()
