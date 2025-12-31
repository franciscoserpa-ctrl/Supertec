import streamlit as st
import pandas as pd
from datetime import datetime
import os
import webbrowser
import urllib.parse
import time

# --- CONFIGURAÇÕES DE ARQUIVOS ---
NOME_ARQUIVO = 'chamados_v3.xlsx'
ARQUIVO_USUARIOS = 'usuarios_v4.xlsx'
ARQUIVO_SETORES = 'setores_v1.xlsx'

def inicializar_arquivos():
    if not os.path.exists(NOME_ARQUIVO):
        colunas = ['ID', 'Cliente', 'Setor', 'Tipo_Problema', 'Urgencia', 'Atendente_Responsavel', 
                   'Direcionado_Para', 'Descricao', 'Status', 'Abertura', 'Fechamento', 'Resolucao']
        pd.DataFrame(columns=colunas).to_excel(NOME_ARQUIVO, index=False)
    
    if not os.path.exists(ARQUIVO_USUARIOS):
        df_user = pd.DataFrame([['master', '123', 'Gerente Master', 'N']], 
                               columns=['usuario', 'senha', 'nome', 'trocar_senha'])
        df_user.to_excel(ARQUIVO_USUARIOS, index=False)

    if not os.path.exists(ARQUIVO_SETORES):
        setores_iniciais = ["SEMUG", "OUVIDORIA", "GABINETE", "SEMAD", "SEMUS", "UMEP", "POLICLINICA", "Outros"]
        pd.DataFrame(setores_iniciais, columns=['Nome']).to_excel(ARQUIVO_SETORES, index=False)

def enviar_notificacao_whatsapp(mensagem):
    texto_codificado = urllib.parse.quote(mensagem)
    link = f"https://web.whatsapp.com/send?text={texto_codificado}"
    webbrowser.open(link)

inicializar_arquivos()

# --- INTERFACE ---
st.set_page_config(page_title="Sistema de Chamados v5.3", layout="wide", page_icon="🎫")

if 'pagina' not in st.session_state: st.session_state.pagina = 'abertura'
if 'logado' not in st.session_state: st.session_state.logado = False

# Navegação
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    if st.button("📝 ABERTURA DE CHAMADO", use_container_width=True): st.session_state.pagina = 'abertura'
with col_nav2:
    if st.button("🛠 PAINEL TÉCNICO", use_container_width=True): st.session_state.pagina = 'tecnico'
with col_nav3:
    if st.button("📊 RELATÓRIOS", use_container_width=True): st.session_state.pagina = 'relatorio'

st.divider()

def gerenciar_sessao():
    df_u = pd.read_excel(ARQUIVO_USUARIOS)
    if not st.session_state.logado:
        with st.sidebar:
            st.title("🔐 Login Técnico")
            u_input = st.text_input("Usuário")
            s_input = st.text_input("Senha", type="password")
            if st.button("Entrar"):
                user_data = df_u[(df_u['usuario'] == u_input) & (df_u['senha'].astype(str) == s_input)]
                if not user_data.empty:
                    st.session_state.logado = True
                    st.session_state.user_atual = u_input
                    st.session_state.nome_atual = user_data.iloc[0]['nome']
                    st.session_state.precisa_trocar = user_data.iloc[0]['trocar_senha'] == 'S'
                    st.rerun()
                else: st.error("Dados inválidos.")
    return st.session_state.logado

# --- TELAS ---

if st.session_state.pagina == 'abertura':
    st.header("📝 Registro de Chamado")
    df_u = pd.read_excel(ARQUIVO_USUARIOS)
    df_s = pd.read_excel(ARQUIVO_SETORES)
    lista_tecnicos = df_u['nome'].tolist()
    lista_setores = sorted(df_s['Nome'].tolist())
    opcoes_direcionar = ["UMEP todos", "Prefeitura todos"] + lista_tecnicos

    with st.form("form_abertura", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            atendente = st.selectbox("Técnico Abertura:", lista_tecnicos)
            cliente = st.text_input("Nome do Solicitante")
            setor = st.selectbox("Setor Origem", lista_setores)
        with c2:
            tipo = st.selectbox("Tipo de Problema", ["Rede", "Hardware", "Internet", "Sistema", "Outros"])
            urgencia = st.radio("Grau de Urgência", ["Prioridade Normal", "Urgente"], horizontal=True)
            direcionado = st.selectbox("Direcionar para:", opcoes_direcionar)
        
        descricao = st.text_area("Descrição do Problema")
        if st.form_submit_button("✅ REGISTRAR E NOTIFICAR"):
            if cliente and descricao:
                df = pd.read_excel(NOME_ARQUIVO)
                novo_id = len(df) + 0000
                agora_str = datetime.now().strftime('%d/%m/%Y %H:%M')
                
                novo_item = {
                    'ID': novo_id, 'Cliente': cliente, 'Setor': setor, 'Tipo_Problema': tipo,
                    'Urgencia': urgencia, 'Atendente_Responsavel': atendente, 
                    'Direcionado_Para': direcionado, 'Descricao': descricao, 'Status': 'Aberto', 
                    'Abertura': agora_str, 'Fechamento': '', 'Resolucao': ''
                }
                pd.concat([df, pd.DataFrame([novo_item])], ignore_index=True).to_excel(NOME_ARQUIVO, index=False)
                
                msg = (f"🚨 *NOVO CHAMADO #{novo_id}*\n"
                       f"👤 *Solicitante:* {cliente}\n"
                       f"⏰ *Aberto em:* {agora_str}\n"
                       f"📍 *Setor:* {setor}\n"
                       f"⚠️ *Urgência:* {urgencia}\n"
                       f"📝 *Descrição:* {descricao}")
                enviar_notificacao_whatsapp(msg)
                st.success(f"Chamado #{novo_id} aberto!")

elif st.session_state.pagina == 'tecnico':
    if gerenciar_sessao():
        st.header(f"🛠 Painel Técnico: {st.session_state.nome_atual}")
        
        # MÓDULOS DO MASTER (USUÁRIOS E SETORES)
        if st.session_state.user_atual == 'master':
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                with st.expander("👑 GERENCIAR USUÁRIOS"):
                    df_u = pd.read_excel(ARQUIVO_USUARIOS)
                    with st.form("cad_tec", clear_on_submit=True):
                        nu, nn, ns = st.text_input("Login"), st.text_input("Nome"), st.text_input("Senha")
                        if st.form_submit_button("Salvar"):
                            new_row = pd.DataFrame([[nu, ns, nn, 'S']], columns=df_u.columns)
                            pd.concat([df_u, new_row], ignore_index=True).to_excel(ARQUIVO_USUARIOS, index=False)
                            st.rerun()
            with col_m2:
                with st.expander("🏢 GERENCIAR SETORES"):
                    df_s = pd.read_excel(ARQUIVO_SETORES)
                    with st.form("cad_setor", clear_on_submit=True):
                        ns_nome = st.text_input("Novo Setor")
                        if st.form_submit_button("Adicionar"):
                            pd.concat([df_s, pd.DataFrame([[ns_nome]], columns=['Nome'])], ignore_index=True).to_excel(ARQUIVO_SETORES, index=False)
                            st.rerun()

        st.divider()
        
        # EXIBIÇÃO DE CHAMADOS ABERTOS
        df = pd.read_excel(NOME_ARQUIVO)
        abertos = df[df['Status'] == 'Aberto']
        
        st.subheader("Chamados em Aberto")
        st.dataframe(abertos, use_container_width=True)
        
        # BOTÃO DE ENCERRAR (RECOLOCADO E CORRIGIDO)
        if not abertos.empty:
            st.markdown("### 🏁 Finalizar um Atendimento")
            with st.expander("Clique aqui para descrever a solução e fechar um chamado", expanded=True):
                with st.form("form_finalizar"):
                    id_sel = st.selectbox("Selecione o ID do Chamado", abertos['ID'].tolist())
                    solucao = st.text_area("Relatório da Solução")
                    
                    if st.form_submit_button("CONCLUIR CHAMADO E NOTIFICAR"):
                        if solucao:
                            idx = df.index[df['ID'] == id_sel].tolist()[0]
                            df.at[idx, 'Status'] = 'Fechado'
                            df.at[idx, 'Fechamento'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                            df.at[idx, 'Resolucao'] = solucao
                            df.to_excel(NOME_ARQUIVO, index=False)
                            
                            msg_fim = (f"✅ *CHAMADO CONCLUÍDO #{id_sel}*\n"
                                       f"👤 *Técnico:* {st.session_state.nome_atual}\n"
                                       f"🛠 *Solução:* {solucao}")
                            enviar_notificacao_whatsapp(msg_fim)
                            st.success(f"Chamado {id_sel} fechado!")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("Escreva a solução antes de fechar.")
        else:
            st.info("Não há chamados abertos no momento.")

elif st.session_state.pagina == 'relatorio':
    if gerenciar_sessao():
        st.header("📊 Histórico e Gestão de Tempo")
        df = pd.read_excel(NOME_ARQUIVO)
        
        def calcular_tempo(row):
            try:
                inicio = datetime.strptime(str(row['Abertura']), '%d/%m/%Y %H:%M')
                fim = datetime.now() if row['Status'] == 'Aberto' else datetime.strptime(str(row['Fechamento']), '%d/%m/%Y %H:%M')
                diff = fim - inicio
                d, h, m = diff.days, diff.seconds // 3600, (diff.seconds // 60) % 60
                return f"{d}d {h}h {m}m" if d > 0 else f"{h}h {m}m"
            except: return "-"

        if not df.empty:
            df['Tempo Decorrido'] = df.apply(calcular_tempo, axis=1)
            cols = ['ID', 'Status', 'Tempo Decorrido', 'Cliente', 'Urgencia', 'Abertura', 'Fechamento', 'Resolucao']
            st.dataframe(df[cols], use_container_width=True)
            
            # Botão para forçar atualização do timer
            if st.button("🔄 Atualizar Timer"):
                st.rerun()