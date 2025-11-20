"""
Portal Performance - Atlas Inovações
Aplicação principal do portal Streamlit
"""

import os
import sys
import warnings

# Suprimir avisos que não impactam a UI
warnings.filterwarnings("ignore", message=".*Data Validation extension is not supported.*")
warnings.filterwarnings("ignore", message=".*Unknown extension is not supported.*")

# Garantir import do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Portal Performance | Atlas Inovações",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:kaike.costa@atlasinovacoes.com.br',
        'About': "Portal Performance v2.0 - Atlas Inovações"
    }
)

# Redireciona para a primeira página (Execução)
try:
    st.switch_page("pages/1_Execução.py")
except Exception:
    # Fallback caso o redirect não funcione
    from portal_streamlit.utils.ui import inject_global_styles, render_sidebar_branding, COLORS
    
    inject_global_styles()
    render_sidebar_branding()
    
    # Tela de boas-vindas
    st.markdown(f"""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
        text-align: center;
        padding: 2rem;
    ">
        <div style="font-size: 5rem; margin-bottom: 1rem;">📊</div>
        
        <h1 style="
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0 0 1rem 0;
        ">Portal Performance</h1>
        
        <p style="
            color: {COLORS['text_secondary']};
            font-size: 1.2rem;
            max-width: 600px;
            line-height: 1.8;
            margin: 0 0 2rem 0;
        ">
            Sistema de automação para envio de medições mensais de shoppings.
            Gerencie, visualize e envie relatórios de forma rápida e segura.
        </p>
        
        <div style="
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            justify-content: center;
        ">
            <a href="/Execução" style="
                background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            ">⚡ Iniciar Execução</a>
            
            <a href="/Preview" style="
                background: transparent;
                color: {COLORS['text_primary']};
                padding: 1rem 2rem;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                border: 2px solid {COLORS['border']};
            ">👁️ Ver Previews</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Cards de funcionalidades
    st.markdown("<hr>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <span style="font-size: 2rem;">⚡</span>
            <h4 style="color: {COLORS['text_primary']}; margin: 0.5rem 0;">Execução</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0;">
                Envie medições
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <span style="font-size: 2rem;">👁️</span>
            <h4 style="color: {COLORS['text_primary']}; margin: 0.5rem 0;">Preview</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0;">
                Visualize e-mails
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <span style="font-size: 2rem;">⚙️</span>
            <h4 style="color: {COLORS['text_primary']}; margin: 0.5rem 0;">Config</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0;">
                Personalize
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
        ">
            <span style="font-size: 2rem;">📋</span>
            <h4 style="color: {COLORS['text_primary']}; margin: 0.5rem 0;">Logs</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0;">
                Histórico
            </p>
        </div>
        """, unsafe_allow_html=True)