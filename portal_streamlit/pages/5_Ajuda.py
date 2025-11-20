"""
Página de Ajuda - Portal Performance
Documentação e suporte
"""

import os
import sys
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles, render_header, COLORS

# Configuração da página
st.set_page_config(
    page_title="Ajuda | Portal Performance",
    page_icon="❓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos
inject_global_styles()
render_sidebar_branding()

# Header
render_header(
    title="Central de Ajuda",
    subtitle="Documentação, tutoriais e suporte",
    icon="❓"
)

# Guia Rápido
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    color: white;
">
    <h2 style="color: white !important; margin: 0 0 1rem 0; font-size: 1.5rem;">🚀 Guia Rápido</h2>
    <p style="color: rgba(255,255,255,0.9) !important; font-size: 1rem; margin: 0; line-height: 1.8;">
        <strong>1.</strong> Acesse <strong>Execução</strong> → Selecione região e unidades → Clique em <strong>Executar</strong><br>
        <strong>2.</strong> Visualize os e-mails em <strong>Preview</strong> antes de enviar<br>
        <strong>3.</strong> Personalize colunas e textos em <strong>Configurações</strong><br>
        <strong>4.</strong> Acompanhe o histórico em <strong>Logs</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Tabs de ajuda
tab1, tab2, tab3, tab4 = st.tabs(["📖 Funcionalidades", "❓ FAQ", "🔧 Solução de Problemas", "📞 Suporte"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            height: 100%;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0;">⚡ Execução</h3>
            <p style="color: {COLORS['text_secondary']}; line-height: 1.8; margin: 0;">
                Execute a automação de envio de medições:
            </p>
            <ul style="color: {COLORS['text_secondary']}; line-height: 2; margin-top: 0.5rem; padding-left: 1.2rem;">
                <li>Selecione região e unidades</li>
                <li>Escolha entre preview (dry-run) ou envio real</li>
                <li>Acompanhe o progresso em tempo real</li>
                <li>Veja os detalhes da execução</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0;">⚙️ Configurações</h3>
            <p style="color: {COLORS['text_secondary']}; line-height: 1.8; margin: 0;">
                Personalize o sistema:
            </p>
            <ul style="color: {COLORS['text_secondary']}; line-height: 2; margin-top: 0.5rem; padding-left: 1.2rem;">
                <li>Configure colunas por unidade</li>
                <li>Defina o mês de referência</li>
                <li>Aplique configurações em lote</li>
                <li>Ajuste caminhos do sistema</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0;">👁️ Preview</h3>
            <p style="color: {COLORS['text_secondary']}; line-height: 1.8; margin: 0;">
                Visualize e edite os e-mails:
            </p>
            <ul style="color: {COLORS['text_secondary']}; line-height: 2; margin-top: 0.5rem; padding-left: 1.2rem;">
                <li>Veja o e-mail antes de enviar</li>
                <li>Edite textos de introdução</li>
                <li>Personalize observações</li>
                <li>Preview em tempo real</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0;">📋 Logs</h3>
            <p style="color: {COLORS['text_secondary']}; line-height: 1.8; margin: 0;">
                Acompanhe o histórico:
            </p>
            <ul style="color: {COLORS['text_secondary']}; line-height: 2; margin-top: 0.5rem; padding-left: 1.2rem;">
                <li>Veja todos os envios realizados</li>
                <li>Filtre por região, unidade ou status</li>
                <li>Exporte relatórios em CSV</li>
                <li>Identifique erros rapidamente</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown(f"""
    <div style="color: {COLORS['text_secondary']};">
    """, unsafe_allow_html=True)
    
    with st.expander("🤔 O que é o modo Dry-run?", expanded=True):
        st.markdown("""
        O **modo Dry-run** (preview) gera os e-mails HTML sem enviá-los de verdade. 
        É útil para:
        - Verificar se os dados estão corretos
        - Revisar o layout do e-mail
        - Testar configurações sem risco
        
        Os arquivos HTML são salvos na pasta `output_html` e podem ser visualizados na aba **Preview**.
        """)
    
    with st.expander("📧 Como ativar o envio real?"):
        st.markdown("""
        Para enviar os e-mails de verdade:
        1. Acesse a aba **Execução**
        2. Ative o toggle **"📤 Envio Real via Outlook"**
        3. Clique em **Executar**
        
        ⚠️ **Importante:** Certifique-se de que o Outlook está configurado corretamente no computador.
        """)
    
    with st.expander("🔄 Posso reenviar um e-mail?"):
        st.markdown("""
        Sim! Por padrão, o sistema impede reenvios para evitar duplicidade.
        Para permitir reenvio:
        1. Marque a opção **"🔄 Permitir Reenvio"** na aba Execução
        2. Execute normalmente
        
        O novo envio será registrado nos Logs com status "Reenviado".
        """)
    
    with st.expander("📊 Como personalizar as colunas do relatório?"):
        st.markdown("""
        1. Acesse **Configurações** → **Colunas do Relatório**
        2. Selecione a região e unidade
        3. Marque/desmarque as colunas desejadas
        4. Escolha se quer aplicar só nessa unidade ou em todas
        5. Clique em **Salvar**
        """)
    
    with st.expander("✏️ Como editar os textos do e-mail?"):
        st.markdown("""
        1. Acesse a aba **Preview**
        2. Selecione a unidade
        3. Edite os campos de **Introdução** e **Observação**
        4. As alterações são salvas automaticamente
        
        Você pode usar HTML básico como `<strong>`, `<em>` e `<br>`.
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown(f"""
    <div style="
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid {COLORS['danger']};
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1rem;
    ">
        <p style="color: {COLORS['danger']}; margin: 0; font-weight: 600;">
            ⚠️ Problemas comuns e soluções
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("❌ Erro: 'Planilha não encontrada'"):
        st.markdown("""
        **Causa:** O sistema não encontrou o arquivo Excel da região.
        
        **Solução:**
        1. Verifique se a planilha existe na pasta configurada
        2. O nome do arquivo deve conter a região (ex: `Medição_RJ_2025.xlsx`)
        3. Confira o caminho em **Configurações** → **Sistema**
        """)
    
    with st.expander("❌ Erro: 'Nenhuma unidade encontrada'"):
        st.markdown("""
        **Causa:** A planilha não contém dados para o mês/unidade selecionados.
        
        **Solução:**
        1. Verifique se o mês de referência está correto
        2. Confira se a unidade existe na aba da região
        3. Verifique se há dados preenchidos na planilha
        """)
    
    with st.expander("❌ Erro: 'Outlook não disponível'"):
        st.markdown("""
        **Causa:** O Microsoft Outlook não está instalado ou configurado.
        
        **Solução:**
        1. Certifique-se de que o Outlook está instalado
        2. Configure uma conta de e-mail no Outlook
        3. Feche e reabra o portal
        
        💡 Alternativa: Use o modo **SendGrid** configurando a API key no `.env`
        """)
    
    with st.expander("❌ Erro: 'Já existe envio registrado'"):
        st.markdown("""
        **Causa:** Um e-mail já foi enviado para essa unidade/mês.
        
        **Solução:**
        - Marque **"🔄 Permitir Reenvio"** na aba Execução
        - Ou verifique nos **Logs** se o envio anterior foi bem-sucedido
        """)

with tab4:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        ">
            <span style="font-size: 3rem;">📧</span>
            <h3 style="color: {COLORS['text_primary']}; margin: 1rem 0 0.5rem 0;">E-mail</h3>
            <p style="color: {COLORS['text_secondary']}; margin: 0;">
                kaike.costa@atlasinovacoes.com.br
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 2rem;
            text-align: center;
        ">
            <span style="font-size: 3rem;">💬</span>
            <h3 style="color: {COLORS['text_primary']}; margin: 1rem 0 0.5rem 0;">Teams</h3>
            <p style="color: {COLORS['text_secondary']}; margin: 0;">
                Kaike Costa - Atlas Inovações
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['bg_card']} 0%, {COLORS['bg_dark']} 100%);
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    ">
        <p style="color: {COLORS['text_secondary']}; margin: 0; font-size: 0.9rem;">
            Portal Performance v2.0 • Desenvolvido por <strong style="color: {COLORS['primary']};">Atlas Inovações</strong> © 2025
        </p>
    </div>
    """, unsafe_allow_html=True)