import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Perícias",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Versão do sistema
VERSAO_SISTEMA = "v30.0"

# Dicionário de tradução para os meses
NOMES_MESES_PT_BR = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# CSS personalizado para melhorar o design
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .version-badge {
        background-color: #28a745;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .stExpander {
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    .calendar-day {
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin: 2px;
    }
    .calendar-has-event {
        background-color: #ffc107;
        font-weight: bold;
    }
    /* CSS para o Calendário Compacto - Ajuste para tamanho padrão */
    .cal-header {
        text-align: center;
        font-weight: bold;
        padding: 5px;
        background-color: #1f77b4;
        color: white;
        border-radius: 3px;
        font-size: 0.85rem;
        height: 35px; /* Altura padrão para o cabeçalho */
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 2px; /* Adiciona margem para afastar do dia anterior/próximo */
    }
    .cal-day, .cal-day-event, .cal-day-normal {
        text-align: center;
        padding: 8px; /* Padding ajustado */
        border-radius: 5px;
        font-size: 0.9rem;
        min-height: 40px; /* Altura mínima para padronizar */
        height: 55px; /* Altura fixa para padronizar o espaço */
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-sizing: border-box; /* Inclui padding e borda no tamanho */
        margin: 2px 2px; /* APLICADO ESPAÇAMENTO: 2px para todos os lados */
    }
    .cal-day-empty {
        background-color: transparent;
        color: transparent;
        height: 55px; /* Altura fixa para padronizar o espaço */
        box-sizing: border-box;
        margin: 2px 2px; /* APLICADO ESPAÇAMENTO */
    }
    .cal-day-normal {
        background-color: rgba(150, 150, 150, 0.1);
        color: #666;
        border: 1px solid rgba(150, 150, 150, 0.2);
    }
    .cal-day-event {
        font-weight: bold;
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.3);
    }
    /* AJUSTE PARA COMPACTAR A LEGENDA DO CALENDÁRIO */
    .st-emotion-cache-1r65zjr { /* Classe do div que contém a legenda */
        margin-top: -10px; /* Reduz espaço acima do primeiro item */
        margin-bottom: -10px; /* Reduz espaço abaixo do último item */
    }
    .st-emotion-cache-16ffz9z { /* Classe do st.markdown que contém o texto da legenda */
        margin-top: -8px; 
        margin-bottom: -8px;
        padding-top: 0px;
        padding-bottom: 0px;
    }
</style>
""", unsafe_allow_html=True)

# Funções do Banco de Dados
def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    
    # Tabela de perícias
    c.execute('''
        CREATE TABLE IF NOT EXISTS pericias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vara TEXT,
            num_processo TEXT,
            classe_acao TEXT,
            data_nomeacao DATE,
            prazo_dias INTEGER,
            data_entrega_laudo DATE,
            num_pessoas_entrevistadas INTEGER,
            valor_previsto REAL,
            valor_recebido REAL,
            status TEXT,
            observacoes TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de entrevistas
    c.execute('''
        CREATE TABLE IF NOT EXISTS entrevistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pericia_id INTEGER,
            data_entrevista DATE,
            hora_entrevista TIME,
            nome_entrevistado TEXT,
            status TEXT DEFAULT 'Pendente',
            FOREIGN KEY (pericia_id) REFERENCES pericias (id) ON DELETE CASCADE
        )
    ''')
    
    # Verificar se a coluna status existe na tabela entrevistas
    c.execute("PRAGMA table_info(entrevistas)")
    columns = [column[1] for column in c.fetchall()]
    if 'status' not in columns:
        c.execute("ALTER TABLE entrevistas ADD COLUMN status TEXT DEFAULT 'Pendente'")
    
    conn.commit()
    conn.close()

def adicionar_pericia(dados):
    """Adiciona uma nova perícia"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO pericias (vara, num_processo, classe_acao, data_nomeacao, 
                            prazo_dias, data_entrega_laudo, num_pessoas_entrevistadas,
                            valor_previsto, valor_recebido, status, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', dados)
    conn.commit()
    pericia_id = c.lastrowid
    conn.close()
    return pericia_id

def adicionar_entrevista(pericia_id, data, hora, nome):
    """Adiciona uma entrevista"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO entrevistas (pericia_id, data_entrevista, hora_entrevista, nome_entrevistado, status)
        VALUES (?, ?, ?, ?, 'Pendente')
    ''', (pericia_id, data, hora, nome))
    conn.commit()
    conn.close()

def listar_pericias(filtro_status=None, filtro_vara=None, busca_processo=None):
    """Lista todas as perícias com filtros"""
    conn = sqlite3.connect('pericias.db')
    query = "SELECT * FROM pericias WHERE 1=1"
    params = []
    
    if filtro_status and filtro_status != "Todos":
        query += " AND status = ?"
        params.append(filtro_status)
    
    if filtro_vara and filtro_vara != "Todas":
        query += " AND vara = ?"
        params.append(filtro_vara)
    
    if busca_processo:
        query += " AND num_processo LIKE ?"
        params.append(f"%{busca_processo}%")
    
    query += " ORDER BY data_nomeacao DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def obter_entrevistas(pericia_id):
    """Obtém entrevistas de uma perícia"""
    conn = sqlite3.connect('pericias.db')
    df = pd.read_sql_query(
        "SELECT * FROM entrevistas WHERE pericia_id = ? ORDER BY data_entrevista, hora_entrevista",
        conn,
        params=(pericia_id,)
    )
    conn.close()
    return df

def obter_proximas_entrevistas():
    """Obtém todas as entrevistas pendentes ordenadas por data"""
    conn = sqlite3.connect('pericias.db')
    query = '''
        SELECT e.*, p.num_processo, p.classe_acao, p.vara
        FROM entrevistas e
        JOIN pericias p ON e.pericia_id = p.id
        WHERE e.status = 'Pendente'
        ORDER BY e.data_entrevista, e.hora_entrevista
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obter_entrevistas_mes(ano, mes):
    """Obtém todas as entrevistas (Pendente ou Realizada) de um mês específico"""
    conn = sqlite3.connect('pericias.db')
    # A query foi simplificada, pois não precisamos mais do status da perícia (p.status)
    query = '''
        SELECT e.*, p.num_processo, p.classe_acao, p.vara
        FROM entrevistas e
        JOIN pericias p ON e.pericia_id = p.id
        WHERE strftime('%Y', e.data_entrevista) = ? 
        AND strftime('%m', e.data_entrevista) = ?
    '''
    df = pd.read_sql_query(query, conn, params=(str(ano), str(mes).zfill(2)))
    conn.close()
    return df

def excluir_pericia(pericia_id):
    """Exclui uma perícia"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute("DELETE FROM pericias WHERE id = ?", (pericia_id,))
    conn.commit()
    conn.close()

def atualizar_status_entrevista(entrevista_id, novo_status):
    """Atualiza o status de uma entrevista"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute("UPDATE entrevistas SET status = ? WHERE id = ?", (novo_status, entrevista_id))
    conn.commit()
    conn.close()

def atualizar_status_pericia(pericia_id, novo_status):
    """Atualiza o status de uma perícia"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute("UPDATE pericias SET status = ? WHERE id = ?", (novo_status, pericia_id))
    conn.commit()
    conn.close()

def finalizar_pericia(pericia_id, data_entrega, valor_recebido):
    """Finaliza uma perícia atualizando data de entrega e valor recebido"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    
    if valor_recebido > 0:
        novo_status = "Recebida"
    else:
        novo_status = "Entregue"
    
    c.execute('''
        UPDATE pericias 
        SET data_entrega_laudo = ?, valor_recebido = ?, status = ?
        WHERE id = ?
    ''', (data_entrega, valor_recebido, novo_status, pericia_id))
    conn.commit()
    conn.close()

def atualizar_valor_recebido(pericia_id, valor_recebido):
    """Atualiza o valor recebido de uma perícia"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute('''
        UPDATE pericias 
        SET valor_recebido = ?, status = 'Recebida'
        WHERE id = ?
    ''', (valor_recebido, pericia_id))
    conn.commit()
    conn.close()

def excluir_entrevista(entrevista_id):
    """Exclui uma entrevista"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute("DELETE FROM entrevistas WHERE id = ?", (entrevista_id,))
    conn.commit()
    conn.close()

def calcular_prazo_restante(data_nomeacao, prazo_dias):
    """Calcula quantos dias restam até o prazo"""
    data_limite = datetime.strptime(data_nomeacao, "%Y-%m-%d") + timedelta(days=prazo_dias)
    dias_restantes = (data_limite - datetime.now()).days
    return dias_restantes, data_limite.strftime("%d/%m/%Y")

def formatar_data(data_str):
    """Converte data de YYYY-MM-DD para DD/MM/YYYY"""
    if data_str and data_str != "None":
        return datetime.strptime(data_str, "%Y-%m-%d").strftime("%d/%m/%Y")
    return "-"

def get_status_color(status):
    """Retorna a cor do status"""
    cores = {
        "Aberto": "#FFA500",      # Laranja
        "Em Revisão": "#FFD700",  # Amarelo/Ouro
        "Entregue": "#1E90FF",    # Azul
        "Recebida": "#32CD32"     # Verde
    }
    return cores.get(status, "#808080")

def obter_dados_financeiros_mes():
    """Obtém dados financeiros agrupados por mês"""
    conn = sqlite3.connect('pericias.db')
    query = '''
        SELECT 
            strftime('%Y-%m', data_nomeacao) as mes_ano,
            SUM(valor_previsto) as total_previsto,
            SUM(valor_recebido) as total_recebido,
            SUM(valor_previsto - valor_recebido) as total_pendente
        FROM pericias
        GROUP BY strftime('%Y-%m', data_nomeacao)
        ORDER BY mes_ano
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obter_contagem_status():
    """Obtém contagem de perícias por status"""
    conn = sqlite3.connect('pericias.db')
    query = '''
        SELECT status, COUNT(*) as quantidade
        FROM pericias
        GROUP BY status
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Inicializar banco de dados
init_db()

# Interface Principal
col_title, col_version = st.columns([6, 1])
with col_title:
    st.markdown('<p class="main-header">📋 Sistema de Gestão de Perícias</p>', unsafe_allow_html=True)
with col_version:
    st.markdown(f'<span class="version-badge">{VERSAO_SISTEMA}</span>', unsafe_allow_html=True)

st.markdown("---")

# Menu lateral
st.sidebar.markdown("### 📌 Menu Principal")

menu = st.sidebar.selectbox(
    "Navegação",
    ["📝 Cadastrar Perícia", "📊 Listar Perícias", "📅 Próximas Entrevistas", "💰 Resumo Financeiro"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Versão:** {VERSAO_SISTEMA}")
st.sidebar.markdown("**Desenvolvido com** ❤️")

# CADASTRAR PERÍCIA
if menu == "📝 Cadastrar Perícia":
    st.header("📝 Cadastrar Nova Perícia")
    
    with st.form("form_pericia"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vara = st.selectbox("Vara *", ["1VF", "2VF", "3VF"])
            num_processo = st.text_input("Nº do Processo *", placeholder="Ex: 0000000-00.0000.0.00.0000")
            classe_acao = st.text_input("Classe da Ação *", placeholder="Ex: Guarda de Família")
        
        with col2:
            data_nomeacao = st.date_input(
                "Data da Nomeação *", 
                value=datetime.now(),
                format="DD/MM/YYYY"
            )
            prazo_dias = st.number_input("Prazo Total (dias) *", min_value=1, value=30)
            num_pessoas = st.number_input("Nº de Pessoas a Entrevistar", min_value=0, value=0)
        
        with col3:
            valor_previsto = st.number_input("Valor Previsto (R$)", min_value=0.0, value=0.0, step=100.0)
            st.info("💡 Data de entrega e valor recebido serão preenchidos ao finalizar a perícia.")
        
        observacoes = st.text_area("Observações")
        
        submit = st.form_submit_button("✅ Cadastrar Perícia", use_container_width=True, type="primary")
        
        if submit:
            if not num_processo or not classe_acao:
                st.error("⚠️ Preencha todos os campos obrigatórios (*)")
            else:
                dados = (
                    vara, num_processo, classe_acao, data_nomeacao.strftime("%Y-%m-%d"),
                    prazo_dias, None, num_pessoas, valor_previsto, 0.0, "Aberto", observacoes
                )
                
                pericia_id = adicionar_pericia(dados)
                st.success(f"✅ Perícia cadastrada com sucesso! ID: {pericia_id}")
                st.info("💡 Acesse 'Listar Perícias' para adicionar entrevistas e gerenciar a perícia.")

# LISTAR PERÍCIAS
elif menu == "📊 Listar Perícias":
    st.header("📊 Perícias Cadastradas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Aberto", "Em Revisão", "Entregue", "Recebida"])
    
    with col2:
        varas_unicas = ["Todas", "1VF", "2VF", "3VF"]
        filtro_vara = st.selectbox("Filtrar por Vara", varas_unicas)
    
    with col3:
        busca_processo = st.text_input("Buscar por Processo", placeholder="Digite o nº do processo")
    
    # Listar perícias
    df_pericias = listar_pericias(
        filtro_status if filtro_status != "Todos" else None,
        filtro_vara if filtro_vara != "Todas" else None,
        busca_processo if busca_processo else None
    )
    
    if df_pericias.empty:
        st.info("📭 Nenhuma perícia cadastrada ainda.")
    else:
        st.markdown(f"**Total de perícias:** {len(df_pericias)}")
        
        # Exibir cada perícia em um expander
        for idx, row in df_pericias.iterrows():
            df_entrevistas = obter_entrevistas(row['id'])
            entrevistas_pendentes = len(df_entrevistas[df_entrevistas['status'] == 'Pendente']) if not df_entrevistas.empty else 0
            
            # Emojis coloridos para status
            emoji_status = {
                "Aberto": "🟠",        # Laranja
                "Em Revisão": "🟡",    # Amarelo
                "Entregue": "🔵",      # Azul
                "Recebida": "🟢"       # Verde
            }
            
            titulo = f"**{row['num_processo']}** | {row['classe_acao']} | 👥 {entrevistas_pendentes} pendente(s) | {emoji_status.get(row['status'], '⚪')} {row['status']} | 💰 R$ {row['valor_recebido']:.2f}"
            
            with st.expander(titulo, expanded=False):
                dias_restantes, data_limite = calcular_prazo_restante(row['data_nomeacao'], row['prazo_dias'])
                cor_prazo = "red" if dias_restantes < 0 else "orange" if dias_restantes <= 7 else "green"
                cor_status = get_status_color(row['status'])
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Vara:** {row['vara']}")
                    st.markdown(f"**Classe:** {row['classe_acao']}")
                    st.markdown(f"**Data Nomeação:** {formatar_data(row['data_nomeacao'])}")
                    st.markdown(f"**Prazo Total:** {row['prazo_dias']} dias")
                    st.markdown(f"**Data Limite:** {data_limite}")
                    st.markdown(f"**Prazo Restante:** <span style='color:{cor_prazo}; font-weight:bold'>{dias_restantes} dias</span>", unsafe_allow_html=True)
                    if row['data_entrega_laudo']:
                        st.markdown(f"**Data Entrega:** {formatar_data(str(row['data_entrega_laudo']))}")
                    st.markdown(f"**Pessoas a Entrevistar:** {row['num_pessoas_entrevistadas']}")
                    st.markdown(f"**Valor Previsto:** R$ {row['valor_previsto']:.2f}")
                    st.markdown(f"**Valor Recebido:** R$ {row['valor_recebido']:.2f}")
                    if row['observacoes']:
                        st.markdown(f"**Observações:** {row['observacoes']}")
                
                with col2:
                    st.markdown(f"<h3 style='color:{cor_status}; text-align:center'>{row['status']}</h3>", unsafe_allow_html=True)
                    
                    # Alterar Status
                    st.markdown("**Alterar Status:**")
                    novo_status = st.selectbox(
                        "Status",
                        ["Aberto", "Em Revisão", "Entregue", "Recebida"],
                        index=["Aberto", "Em Revisão", "Entregue", "Recebida"].index(row['status']),
                        key=f"status_{row['id']}",
                        label_visibility="collapsed"
                    )
                    
                    if novo_status != row['status']:
                        if novo_status == "Recebida":
                            if st.button("💾 Salvar", key=f"save_status_{row['id']}", use_container_width=True):
                                st.session_state[f'status_recebida_{row["id"]}'] = True
                        else:
                            if st.button("💾 Salvar", key=f"save_status_{row['id']}", use_container_width=True):
                                atualizar_status_pericia(row['id'], novo_status)
                                st.success(f"Status alterado para: {novo_status}")
                                st.rerun()
                    
                    st.markdown("---")
                    
                    if row['status'] in ["Aberto", "Em Revisão"]:
                        if st.button("✅ Finalizar Perícia", key=f"fin_{row['id']}", use_container_width=True):
                            st.session_state[f'finalizar_{row["id"]}'] = True
                    
                    if row['status'] == "Entregue":
                        if st.button("💰 Registrar Pagamento", key=f"pag_{row['id']}", use_container_width=True):
                            st.session_state[f'pagamento_{row["id"]}'] = True
                    
                    if st.button("🗑️ Excluir", key=f"del_{row['id']}", use_container_width=True):
                        excluir_pericia(row['id'])
                        st.rerun()
                
                # Modal para mudar status para Recebida
                if st.session_state.get(f'status_recebida_{row["id"]}', False):
                    st.markdown("---")
                    st.subheader("💰 Registrar como Recebida")
                    with st.form(f"form_status_recebida_{row['id']}"):
                        valor_rec = st.number_input("Valor Recebido (R$) *", min_value=0.0, value=row['valor_previsto'], step=100.0)
                        
                        col_sr1, col_sr2 = st.columns(2)
                        with col_sr1:
                            if st.form_submit_button("✅ Confirmar", use_container_width=True):
                                atualizar_valor_recebido(row['id'], valor_rec)
                                st.session_state[f'status_recebida_{row["id"]}'] = False
                                st.success("Status alterado para Recebida!")
                                st.rerun()
                        with col_sr2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f'status_recebida_{row["id"]}'] = False
                                st.rerun()
                
                # Modal para finalizar perícia
                if st.session_state.get(f'finalizar_{row["id"]}', False):
                    st.markdown("---")
                    st.subheader("📝 Finalizar Perícia")
                    with st.form(f"form_finalizar_{row['id']}"):
                        data_entrega = st.date_input(
                            "Data de Entrega do Laudo *", 
                            value=datetime.now(),
                            format="DD/MM/YYYY"
                        )
                        valor_recebido = st.number_input("Valor Recebido (R$)", min_value=0.0, value=0.0, step=100.0)
                        
                        col_fin1, col_fin2 = st.columns(2)
                        with col_fin1:
                            if st.form_submit_button("✅ Confirmar", use_container_width=True):
                                finalizar_pericia(row['id'], data_entrega.strftime("%Y-%m-%d"), valor_recebido)
                                st.session_state[f'finalizar_{row["id"]}'] = False
                                st.success("Perícia finalizada!")
                                st.rerun()
                        with col_fin2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f'finalizar_{row["id"]}'] = False
                                st.rerun()
                
                # Modal para registrar pagamento
                if st.session_state.get(f'pagamento_{row["id"]}', False):
                    st.markdown("---")
                    st.subheader("💰 Registrar Pagamento")
                    with st.form(f"form_pagamento_{row['id']}"):
                        valor_recebido = st.number_input("Valor Recebido (R$) *", min_value=0.0, value=row['valor_previsto'], step=100.0)
                        
                        col_pag1, col_pag2 = st.columns(2)
                        with col_pag1:
                            if st.form_submit_button("✅ Confirmar", use_container_width=True):
                                atualizar_valor_recebido(row['id'], valor_recebido)
                                st.session_state[f'pagamento_{row["id"]}'] = False
                                st.success("Pagamento registrado!")
                                st.rerun()
                        with col_pag2:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state[f'pagamento_{row["id"]}'] = False
                                st.rerun()
                
                # Entrevistas
                st.markdown("---")
                st.markdown("### 👥 Entrevistas")
                
                if not df_entrevistas.empty:
                    for ent_idx, ent in df_entrevistas.iterrows():
                        col_ent1, col_ent2, col_ent3 = st.columns([3, 1, 1])
                        
                        status_ent = ent['status'] if 'status' in ent else 'Pendente'
                        cor_ent = "green" if status_ent == "Realizada" else "orange"
                        
                        with col_ent1:
                            st.markdown(f"📅 **{formatar_data(ent['data_entrevista'])}** às **{ent['hora_entrevista']}** - {ent['nome_entrevistado']} | <span style='color:{cor_ent}'>● {status_ent}</span>", unsafe_allow_html=True)
                        
                        with col_ent2:
                            novo_status = "Realizada" if status_ent == "Pendente" else "Pendente"
                            if st.button(f"{'✓' if status_ent == 'Pendente' else '↺'}", key=f"status_ent_{ent['id']}", help=f"Marcar como {novo_status}"):
                                atualizar_status_entrevista(ent['id'], novo_status)
                                st.rerun()
                        
                        with col_ent3:
                            if st.button("🗑️", key=f"del_ent_{ent['id']}"):
                                excluir_entrevista(ent['id'])
                                st.rerun()
                else:
                    st.info("Nenhuma entrevista cadastrada.")
                
                # Adicionar nova entrevista
                with st.form(f"form_entrevista_{row['id']}"):
                    st.markdown("**➕ Adicionar Entrevista**")
                    col_e1, col_e2, col_e3 = st.columns(3)
                    
                    with col_e1:
                        data_ent = st.date_input("Data *", key=f"data_{row['id']}", format="DD/MM/YYYY")
                    with col_e2:
                        hora_ent = st.time_input("Hora *", key=f"hora_{row['id']}")
                    with col_e3:
                        nome_ent = st.text_input("Nome *", key=f"nome_{row['id']}")
                    
                    if st.form_submit_button("➕ Adicionar", use_container_width=True):
                        if nome_ent:
                            adicionar_entrevista(row['id'], data_ent.strftime("%Y-%m-%d"), hora_ent.strftime("%H:%M"), nome_ent)
                            st.success("Entrevista adicionada!")
                            st.rerun()
                        else:
                            st.error("Preencha todos os campos!")

# PRÓXIMAS ENTREVISTAS
elif menu == "📅 Próximas Entrevistas":
    st.header("📅 Próximas Entrevistas Agendadas")
    
    df_entrevistas_pendentes = obter_proximas_entrevistas()
    total_pendentes = len(df_entrevistas_pendentes)
    
    # Métricas
    col_metric1, col_metric2 = st.columns(2)
    with col_metric1:
        st.metric("📋 Total de Entrevistas Pendentes", total_pendentes)
    with col_metric2:
        if not df_entrevistas_pendentes.empty:
            proxima = df_entrevistas_pendentes.iloc[0]
            proxima_data = datetime.strptime(proxima['data_entrevista'], "%Y-%m-%d").strftime("%d/%m/%Y")
            nome_entrevistado = proxima['nome_entrevistado']
            st.metric("🔔 Próxima Entrevista", f"{nome_entrevistado} em {proxima_data} às {proxima['hora_entrevista']}")
    
    st.markdown("---")
    
    # Calendário
    st.subheader("📆 Calendário de Entrevistas")
    
    # Inicializar estado do calendário
    if 'cal_mes' not in st.session_state:
        st.session_state.cal_mes = datetime.now().month
    if 'cal_ano' not in st.session_state:
        st.session_state.cal_ano = datetime.now().year
    
    # Controles de navegação
    col_prev, col_ano, col_titulo, col_next, col_hoje = st.columns([1, 1.5, 2.5, 1, 1.5])
    
    with col_prev:
        if st.button("◀", use_container_width=True, help="Mês anterior"):
            if st.session_state.cal_mes == 1:
                st.session_state.cal_mes = 12
                st.session_state.cal_ano -= 1
            else:
                st.session_state.cal_mes -= 1
            st.rerun()
    
    with col_ano:
        ano_novo = st.selectbox(
            "Ano",
            list(range(2020, 2035)),
            index=st.session_state.cal_ano - 2020,
            key="select_ano",
            label_visibility="collapsed"
        )
        if ano_novo != st.session_state.cal_ano:
            st.session_state.cal_ano = ano_novo
            st.rerun()
    
    with col_titulo:
        mes_nome = NOMES_MESES_PT_BR.get(st.session_state.cal_mes, str(st.session_state.cal_mes))
        st.markdown(f"<h3 style='text-align:center; margin:0'>{mes_nome} de {st.session_state.cal_ano}</h3>", unsafe_allow_html=True)
    
    with col_next:
        if st.button("▶", use_container_width=True, help="Próximo mês"):
            if st.session_state.cal_mes == 12:
                st.session_state.cal_mes = 1
                st.session_state.cal_ano += 1
            else:
                st.session_state.cal_mes += 1
            st.rerun()
    
    with col_hoje:
        if st.button("📅 Hoje", use_container_width=True):
            st.session_state.cal_mes = datetime.now().month
            st.session_state.cal_ano = datetime.now().year
            st.rerun()
    
    # Obter TODAS as entrevistas do mês (para calcular pendentes)
    df_entrevistas_mes = obter_entrevistas_mes(st.session_state.cal_ano, st.session_state.cal_mes)
    
    # Criar calendário visual compacto
    cal = calendar.monthcalendar(st.session_state.cal_ano, st.session_state.cal_mes)
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    
    # Cabeçalho do calendário
    cols_header = st.columns(7)
    for idx, dia in enumerate(dias_semana):
        with cols_header[idx]:
            st.markdown(f"<div class='cal-header'>{dia}</div>", unsafe_allow_html=True)
    
    # Dias do calendário
    for semana in cal:
        cols = st.columns(7)
        for idx, dia in enumerate(semana):
            with cols[idx]:
                if dia == 0:
                    st.markdown("<div class='cal-day cal-day-empty'> </div>", unsafe_allow_html=True)
                else:
                    # 1. Montar a data para busca
                    data_busca = f"{st.session_state.cal_ano}-{str(st.session_state.cal_mes).zfill(2)}-{str(dia).zfill(2)}"
                    
                    # 2. Filtrar entrevistas do dia
                    entrevistas_dia = df_entrevistas_mes[df_entrevistas_mes['data_entrevista'] == data_busca]
                    
                    if not entrevistas_dia.empty:
                        # 3. Contar entrevistas pendentes
                        count_pendente = len(entrevistas_dia[entrevistas_dia['status'] == 'Pendente'])
                        count_total = len(entrevistas_dia)

                        # 4. Definir a cor baseada no status das entrevistas
                        if count_pendente > 0:
                            # Se houver PENDENTE, cor Laranja (Entrevista Agendada)
                            cor_dia = "#FFA500" # Laranja
                            badge_text = f"{count_pendente} 🟡"
                        else:
                            # Se todas as TOTAL estiverem Realizadas, cor Verde (Concluído)
                            cor_dia = "#32CD32" # Verde
                            badge_text = f"{count_total} ✓"
                            
                        # 5. Exibir o dia e a contagem de PENDENTES/TOTAL
                        st.markdown(f"<div class='cal-day cal-day-event' style='background-color:{cor_dia}'>{dia}<br><small>{badge_text}</small></div>", unsafe_allow_html=True)
                    else:
                        # Dia sem entrevistas
                        st.markdown(f"<div class='cal-day cal-day-normal'>{dia}</div>", unsafe_allow_html=True)
    
    # Legenda (Atualizada para refletir a lógica de entrevista)
    st.markdown("---")
    st.markdown("**Legenda (Calendário de Entrevistas):**")
    col_leg1, col_leg2 = st.columns(2)
    with col_leg1:
        st.markdown("<div class='st-emotion-cache-16ffz9z'>🟡 Pendente</div>", unsafe_allow_html=True)
    with col_leg2:
        st.markdown("<div class='st-emotion-cache-16ffz9z'>✓ Concluída</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Lista de entrevistas (Usa df_entrevistas_pendentes)
    if df_entrevistas_pendentes.empty:
        st.info("📭 Nenhuma entrevista pendente.")
    else:
        st.subheader("📋 Lista de Entrevistas Pendentes")
        
        df_entrevistas_pendentes['data_entrevista'] = pd.to_datetime(df_entrevistas_pendentes['data_entrevista'])
        df_entrevistas_pendentes = df_entrevistas_pendentes.sort_values('data_entrevista')
        
        data_atual = None
        hoje = datetime.now().date()
        
        for idx, ent in df_entrevistas_pendentes.iterrows():
            data_ent = ent['data_entrevista'].date()
            
            if data_atual != data_ent:
                data_atual = data_ent
                dias_ate = (data_ent - hoje).days
                
                if dias_ate == 0:
                    label_data = "🔴 HOJE"
                elif dias_ate == 1:
                    label_data = "🟡 AMANHÃ"
                elif dias_ate < 0:
                    label_data = f"🔴 ATRASADA ({abs(dias_ate)} dias)"
                elif dias_ate <= 7:
                    label_data = f"🟡 Em {dias_ate} dias"
                else:
                    label_data = f"🟢 Em {dias_ate} dias"
                
                st.markdown(f"### 📅 {data_ent.strftime('%d/%m/%Y')} - {label_data}")
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"""
                **{ent['hora_entrevista']}** - {ent['nome_entrevistado']}  
                *Processo:* {ent['num_processo']} | *Vara:* {ent['vara']} | *Classe:* {ent['classe_acao']}
                """)
            with col2:
                if st.button("✓ Marcar Realizada", key=f"marcar_{ent['id']}"):
                    atualizar_status_entrevista(ent['id'], "Realizada")
                    st.rerun()
            
            st.markdown("---")

# RESUMO FINANCEIRO
elif menu == "💰 Resumo Financeiro":
    st.header("💰 Resumo Financeiro")
    
    df_pericias = listar_pericias()
    
    if df_pericias.empty:
        st.info("📭 Nenhuma perícia cadastrada ainda.")
    else:
        # Métricas principais
        total_previsto = df_pericias['valor_previsto'].sum()
        total_recebido = df_pericias['valor_recebido'].sum()
        total_pendente = total_previsto - total_recebido
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💰 Total Previsto", f"R$ {total_previsto:,.2f}")
        
        with col2:
            st.metric("✅ Total Recebido", f"R$ {total_recebido:,.2f}")
        
        with col3:
            st.metric("⏳ Pendente", f"R$ {total_pendente:,.2f}")
        
        st.markdown("---")
        
        # Gráficos
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.subheader("📊 Valores Financeiros por Mês")
            df_financeiro = obter_dados_financeiros_mes()
            
            if not df_financeiro.empty:
                df_financeiro['mes_ano_formatado'] = pd.to_datetime(df_financeiro['mes_ano']).dt.strftime('%m/%Y')
                
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=df_financeiro['mes_ano_formatado'],
                    y=df_financeiro['total_previsto'],
                    name='Previsto',
                    marker_color='#1f77b4'
                ))
                
                fig.add_trace(go.Bar(
                    x=df_financeiro['mes_ano_formatado'],
                    y=df_financeiro['total_recebido'],
                    name='Recebido',
                    marker_color='#2ca02c'
                ))
                
                fig.add_trace(go.Bar(
                    x=df_financeiro['mes_ano_formatado'],
                    y=df_financeiro['total_pendente'],
                    name='Pendente',
                    marker_color='#ff7f0e'
                ))
                
                fig.update_layout(
                    barmode='group',
                    xaxis_title='Mês/Ano',
                    yaxis_title='Valor (R$)',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum dado financeiro disponível.")
        
        with col_graf2:
            st.subheader("📈 Perícias por Status")
            df_status = obter_contagem_status()
            
            if not df_status.empty:
                cores_status = {
                    'Aberto': '#FFA500',
                    'Em Revisão': '#FFD700',
                    'Entregue': '#1E90FF',
                    'Recebida': '#32CD32'
                }
                
                cores = [cores_status.get(status, '#808080') for status in df_status['status']]
                
                fig = go.Figure(data=[go.Pie(
                    labels=df_status['status'],
                    values=df_status['quantidade'],
                    marker=dict(colors=cores),
                    hole=0.4,
                    textinfo='label+percent+value',
                    textposition='auto'
                )])
                
                fig.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Nenhum dado de status disponível.")
        
        st.markdown("---")
        
        # Perícias com pagamento pendente
        df_pendentes = df_pericias[df_pericias['valor_recebido'] < df_pericias['valor_previsto']]
        
        if not df_pendentes.empty:
            st.subheader("💵 Perícias com Pagamento Pendente")
            
            for idx, row in df_pendentes.iterrows():
                pendente = row['valor_previsto'] - row['valor_recebido']
                
                # Barra de progresso
                percentual = (row['valor_recebido'] / row['valor_previsto'] * 100) if row['valor_previsto'] > 0 else 0
                
                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    st.markdown(f"**{row['num_processo']}** ({row['status']})")
                    st.progress(percentual / 100)
                    st.caption(f"Recebido: R$ {row['valor_recebido']:,.2f} / Previsto: R$ {row['valor_previsto']:,.2f}")
                with col_p2:
                    st.metric("Pendente", f"R$ {pendente:,.2f}")
                
                st.markdown("---")