import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import calendar

# Configuração da página
st.set_page_config(
    page_title="Sistema de Gestão de Perícias",
    page_icon="📋",
    layout="wide"
)

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
    
    # Tabela de entrevistas - Adicionar coluna status se não existir
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

def finalizar_pericia(pericia_id, data_entrega, valor_recebido):
    """Finaliza uma perícia atualizando data de entrega e valor recebido"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    
    # Determinar o novo status baseado no valor recebido
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

def atualizar_status_pericia(pericia_id, novo_status):
    """Atualiza o status de uma perícia"""
    conn = sqlite3.connect('pericias.db')
    c = conn.cursor()
    c.execute("UPDATE pericias SET status = ? WHERE id = ?", (novo_status, pericia_id))
    conn.commit()
    conn.close()

# Inicializar banco de dados
init_db()

# Interface Principal
st.title("📋 Sistema de Gestão de Perícias")
st.markdown("---")

# Menu lateral
menu = st.sidebar.selectbox(
    "Menu",
    ["📝 Cadastrar Perícia", "📊 Listar Perícias", "📅 Próximas Entrevistas", "💰 Resumo Financeiro"]
)

# CADASTRAR PERÍCIA
if menu == "📝 Cadastrar Perícia":
    st.header("Cadastrar Nova Perícia")
    
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
        
        submit = st.form_submit_button("✅ Cadastrar Perícia", use_container_width=True)
        
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
    st.header("Perícias Cadastradas")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Aberto", "Em Revisão", "Entregue", "Recebida"])
    
    with col2:
        df_temp = listar_pericias()
        varas_unicas = ["Todas"] + ["1VF", "2VF", "3VF"]
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
            # Obter entrevistas para contar pendentes
            df_entrevistas = obter_entrevistas(row['id'])
            entrevistas_pendentes = len(df_entrevistas[df_entrevistas['status'] == 'Pendente']) if not df_entrevistas.empty else 0
            
            # Título do expander com informações resumidas
            cor_status = get_status_color(row['status'])
            
            # Emojis coloridos para status
            emoji_status = {
                "Aberto": "🟠",        # Laranja
                "Em Revisão": "🟡",    # Amarelo
                "Entregue": "🔵",      # Azul
                "Recebida": "🟢"       # Verde
            }
            
            titulo = f"**{row['num_processo']}** | {row['classe_acao']} | 👥 {entrevistas_pendentes} pendente(s) | {emoji_status.get(row['status'], '⚪')} {row['status']} | 💰 R$ {row['valor_recebido']:.2f}"
            
            with st.expander(titulo, expanded=False):
                # Calcular prazo restante
                dias_restantes, data_limite = calcular_prazo_restante(row['data_nomeacao'], row['prazo_dias'])
                cor_prazo = "red" if dias_restantes < 0 else "orange" if dias_restantes <= 7 else "green"
                
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
                            # Se mudar para Recebida, pedir valor
                            if st.button("💾 Salvar", key=f"save_status_{row['id']}", use_container_width=True):
                                st.session_state[f'status_recebida_{row["id"]}'] = True
                        else:
                            if st.button("💾 Salvar", key=f"save_status_{row['id']}", use_container_width=True):
                                atualizar_status_pericia(row['id'], novo_status)
                                st.success(f"Status alterado para: {novo_status}")
                                st.rerun()
                    
                    st.markdown("---")
                    
                    # Botões de ação
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
    st.header("Próximas Entrevistas Agendadas")
    
    df_entrevistas = obter_proximas_entrevistas()
    
    if df_entrevistas.empty:
        st.info("📭 Nenhuma entrevista pendente.")
    else:
        st.markdown(f"**Total de entrevistas pendentes:** {len(df_entrevistas)}")
        st.markdown("---")
        
        # Agrupar por data
        df_entrevistas['data_entrevista'] = pd.to_datetime(df_entrevistas['data_entrevista'])
        df_entrevistas = df_entrevistas.sort_values('data_entrevista')
        
        data_atual = None
        hoje = datetime.now().date()
        
        for idx, ent in df_entrevistas.iterrows():
            data_ent = ent['data_entrevista'].date()
            
            # Cabeçalho de data
            if data_atual != data_ent:
                data_atual = data_ent
                dias_ate = (data_ent - hoje).days
                
                if dias_ate == 0:
                    label_data = "🔴 HOJE"
                elif dias_ate == 1:
                    label_data = "🟠 AMANHÃ"
                elif dias_ate < 0:
                    label_data = f"🔴 ATRASADA ({abs(dias_ate)} dias)"
                elif dias_ate <= 7:
                    label_data = f"🟡 Em {dias_ate} dias"
                else:
                    label_data = f"🟢 Em {dias_ate} dias"
                
                st.markdown(f"### 📅 {data_ent.strftime('%d/%m/%Y')} - {label_data}")
            
            # Detalhes da entrevista
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
    st.header("Resumo Financeiro")
    
    df_pericias = listar_pericias()
    
    if df_pericias.empty:
        st.info("📭 Nenhuma perícia cadastrada ainda.")
    else:
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
        
        # Perícias com pagamento pendente
        df_pendentes = df_pericias[df_pericias['valor_recebido'] < df_pericias['valor_previsto']]
        
        if not df_pendentes.empty:
            st.subheader("💵 Perícias com Pagamento Pendente")
            
            for idx, row in df_pendentes.iterrows():
                pendente = row['valor_previsto'] - row['valor_recebido']
                st.markdown(f"🔸 **{row['num_processo']}** ({row['status']}) - Pendente: R$ {pendente:,.2f}")

st.sidebar.markdown("---")
st.sidebar.markdown("**Sistema v2.0** | Desenvolvido com ❤️")