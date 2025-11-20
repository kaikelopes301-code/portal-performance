"""
UI Components - Portal Performance
Design system moderno e profissional
"""

import os
import streamlit as st

# Cores do tema
COLORS = {
    "primary": "#6366f1",      # Indigo
    "primary_dark": "#4f46e5",
    "secondary": "#8b5cf6",    # Violet
    "success": "#10b981",      # Emerald
    "warning": "#f59e0b",      # Amber
    "danger": "#ef4444",       # Red
    "bg_dark": "#0f172a",      # Slate 900
    "bg_card": "#1e293b",      # Slate 800
    "bg_hover": "#334155",     # Slate 700
    "text_primary": "#f8fafc", # Slate 50
    "text_secondary": "#94a3b8", # Slate 400
    "border": "#334155",       # Slate 700
}

def inject_global_styles():
    """Injeta estilos globais modernos no portal."""
    st.markdown(f"""
    <style>
    /* ========== IMPORTAR FONTE ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ========== RESET & BASE ========== */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }}
    
    /* ========== FUNDO PRINCIPAL ========== */
    .stApp {{
        background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, #1a1a2e 100%);
    }}
    
    /* ========== SIDEBAR ========== */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['bg_card']} 0%, {COLORS['bg_dark']} 100%);
        border-right: 1px solid {COLORS['border']};
    }}
    
    section[data-testid="stSidebar"] > div {{
        padding-top: 1rem;
    }}
    
    /* Esconde navegação padrão */
    section[data-testid="stSidebarNav"],
    div[data-testid="stSidebarNav"],
    nav[data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* ========== TÍTULOS ========== */
    h1 {{
        color: {COLORS['text_primary']} !important;
        font-weight: 800 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.5rem !important;
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    h2 {{
        color: {COLORS['text_primary']} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin-top: 1.5rem !important;
    }}
    
    h3 {{
        color: {COLORS['text_secondary']} !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
    }}
    
    /* ========== TEXTO ========== */
    p, span, label, .stMarkdown {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* ========== CARDS (CONTAINERS) ========== */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 16px !important;
        padding: 1.5rem !important;
    }}
    
    /* ========== INPUTS ========== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {{
        background: {COLORS['bg_dark']} !important;
        border: 2px solid {COLORS['border']} !important;
        border-radius: 12px !important;
        color: {COLORS['text_primary']} !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {COLORS['primary']} !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }}
    
    /* ========== SELECTBOX ========== */
    .stSelectbox [data-baseweb="select"] {{
        background: {COLORS['bg_dark']} !important;
    }}
    
    .stSelectbox [data-baseweb="select"] > div {{
        background: {COLORS['bg_dark']} !important;
        border: 2px solid {COLORS['border']} !important;
        border-radius: 12px !important;
    }}
    
    /* ========== MULTISELECT ========== */
    .stMultiSelect [data-baseweb="tag"] {{
        background: {COLORS['primary']} !important;
        border-radius: 8px !important;
    }}
    
    /* ========== BOTÕES ========== */
    .stButton > button {{
        background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(0) !important;
    }}
    
    /* Botão secundário */
    .stButton > button[kind="secondary"] {{
        background: transparent !important;
        border: 2px solid {COLORS['border']} !important;
        color: {COLORS['text_primary']} !important;
        box-shadow: none !important;
    }}
    
    /* ========== TOGGLE/SWITCH ========== */
    .stCheckbox > label > div[data-testid="stCheckbox"] {{
        background: {COLORS['bg_dark']} !important;
    }}
    
    /* ========== PROGRESS BAR ========== */
    .stProgress > div > div > div {{
        background: linear-gradient(90deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%) !important;
        border-radius: 10px !important;
    }}
    
    .stProgress > div > div {{
        background: {COLORS['bg_dark']} !important;
        border-radius: 10px !important;
    }}
    
    /* ========== ALERTS ========== */
    .stSuccess {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%) !important;
        border: 1px solid {COLORS['success']} !important;
        border-radius: 12px !important;
        color: {COLORS['success']} !important;
    }}
    
    .stError {{
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%) !important;
        border: 1px solid {COLORS['danger']} !important;
        border-radius: 12px !important;
    }}
    
    .stWarning {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%) !important;
        border: 1px solid {COLORS['warning']} !important;
        border-radius: 12px !important;
    }}
    
    .stInfo {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
        border: 1px solid {COLORS['primary']} !important;
        border-radius: 12px !important;
    }}
    
    /* ========== DATAFRAME ========== */
    .stDataFrame {{
        border-radius: 12px !important;
        overflow: hidden !important;
    }}
    
    .stDataFrame [data-testid="stDataFrameResizable"] {{
        border: 1px solid {COLORS['border']} !important;
        border-radius: 12px !important;
    }}
    
    /* ========== EXPANDER ========== */
    .streamlit-expanderHeader {{
        background: {COLORS['bg_card']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-radius: 12px !important;
        color: {COLORS['text_primary']} !important;
        font-weight: 600 !important;
    }}
    
    .streamlit-expanderContent {{
        background: {COLORS['bg_dark']} !important;
        border: 1px solid {COLORS['border']} !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }}
    
    /* ========== TABS ========== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: {COLORS['bg_card']} !important;
        padding: 8px !important;
        border-radius: 12px !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent !important;
        border-radius: 8px !important;
        color: {COLORS['text_secondary']} !important;
        font-weight: 500 !important;
        padding: 10px 20px !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background: {COLORS['primary']} !important;
        color: white !important;
    }}
    
    /* ========== DIVIDER ========== */
    hr {{
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, {COLORS['border']}, transparent) !important;
        margin: 2rem 0 !important;
    }}
    
    /* ========== METRICS ========== */
    [data-testid="stMetricValue"] {{
        color: {COLORS['text_primary']} !important;
        font-weight: 700 !important;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {COLORS['text_secondary']} !important;
    }}
    
    /* ========== SCROLLBAR ========== */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {COLORS['bg_dark']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {COLORS['border']};
        border-radius: 4px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {COLORS['bg_hover']};
    }}
    
    /* ========== ANIMAÇÕES ========== */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .main .block-container {{
        animation: fadeIn 0.5s ease-out;
    }}
    
    /* ========== PAGE LINKS (SIDEBAR) ========== */
    a[data-testid="stPageLink-NavLink"] {{
        background: transparent !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        margin: 2px 0 !important;
        transition: all 0.2s ease !important;
        border-left: 3px solid transparent !important;
    }}
    
    a[data-testid="stPageLink-NavLink"]:hover {{
        background: {COLORS['bg_hover']} !important;
        border-left-color: {COLORS['primary']} !important;
    }}
    
    a[data-testid="stPageLink-NavLink"] span {{
        color: {COLORS['text_secondary']} !important;
        font-weight: 500 !important;
    }}
    
    a[data-testid="stPageLink-NavLink"]:hover span {{
        color: {COLORS['text_primary']} !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_sidebar_branding(title: str = "Portal Performance", subtitle: str = "Atlas Inovações"):
    """Renderiza sidebar com branding moderno."""
    
    logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo-atlas.png"))
    
    with st.sidebar:
        # Logo
        try:
            st.image(logo_path, use_container_width=True)
        except Exception:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                margin-bottom: 1rem;
            ">
                <span style="font-size: 2rem;">📊</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Título estilizado
        st.markdown(f"""
        <div style="margin: 1rem 0 0.5rem 0;">
            <h2 style="
                margin: 0;
                font-size: 1.4rem;
                font-weight: 800;
                background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            ">{title}</h2>
            <p style="
                margin: 4px 0 0 0;
                font-size: 0.85rem;
                color: {COLORS['text_secondary']};
                font-weight: 500;
            ">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        # Navegação
        st.markdown(f"""
        <p style="
            font-size: 0.7rem;
            font-weight: 600;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin: 0 0 0.5rem 0.5rem;
        ">Menu</p>
        """, unsafe_allow_html=True)
        
        st.page_link("pages/1_Execução.py", label="⚡ Execução", icon=None)
        st.page_link("pages/2_Preview.py", label="👁️ Preview", icon=None)
        st.page_link("pages/3_Configurações.py", label="⚙️ Configurações", icon=None)
        st.page_link("pages/4_Logs.py", label="📋 Logs", icon=None)
        st.page_link("pages/5_Ajuda.py", label="❓ Ajuda", icon=None)
        
        # Rodapé da sidebar
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="
            position: absolute;
            bottom: 1rem;
            left: 1rem;
            right: 1rem;
            padding-top: 1rem;
            border-top: 1px solid {COLORS['border']};
        ">
            <p style="
                font-size: 0.7rem;
                color: {COLORS['text_secondary']};
                text-align: center;
                margin: 0;
            ">v2.0 • Atlas Inovações © 2025</p>
        </div>
        """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = None, icon: str = None):
    """Renderiza header de página estilizado."""
    icon_html = f"<span style='font-size: 2.5rem; margin-right: 1rem;'>{icon}</span>" if icon else ""
    subtitle_html = f"<p style='color: {COLORS['text_secondary']}; font-size: 1.1rem; margin: 0.5rem 0 0 0;'>{subtitle}</p>" if subtitle else ""
    
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <div style="display: flex; align-items: center;">
            {icon_html}
            <h1 style="margin: 0;">{title}</h1>
        </div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Renderiza card de métrica estilizado."""
    delta_html = ""
    if delta:
        color = COLORS['success'] if delta_color == "good" else COLORS['danger'] if delta_color == "bad" else COLORS['text_secondary']
        delta_html = f"<p style='color: {color}; font-size: 0.85rem; margin: 0.5rem 0 0 0;'>{delta}</p>"
    
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
    ">
        <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0; text-transform: uppercase; letter-spacing: 0.05em;">{label}</p>
        <p style="color: {COLORS['text_primary']}; font-size: 2rem; font-weight: 700; margin: 0.5rem 0 0 0;">{value}</p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_status_badge(status: str, text: str = None):
    """Renderiza badge de status."""
    colors = {
        "success": (COLORS['success'], "rgba(16, 185, 129, 0.1)"),
        "warning": (COLORS['warning'], "rgba(245, 158, 11, 0.1)"),
        "error": (COLORS['danger'], "rgba(239, 68, 68, 0.1)"),
        "info": (COLORS['primary'], "rgba(99, 102, 241, 0.1)"),
    }
    fg, bg = colors.get(status, colors['info'])
    display_text = text or status.capitalize()
    
    return f"""
    <span style="
        background: {bg};
        color: {fg};
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid {fg};
    ">{display_text}</span>
    """