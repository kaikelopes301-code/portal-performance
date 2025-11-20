"""
Página de Configurações - Portal Performance
Gerenciamento de preferências por unidade
"""

import os
import sys
import re
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config, save_config, get_units_overrides, save_unit_override
from portal_streamlit.utils.pipeline import get_regions, list_units_for_region
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles, render_header, COLORS

# Configuração da página
st.set_page_config(
    page_title="Configurações | Portal Performance",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos
inject_global_styles()
render_sidebar_branding()

# Header
render_header(
    title="Configurações",
    subtitle="Personalize colunas e preferências por unidade",
    icon="⚙️"
)

# Carregar configurações
config = get_config()

# Tabs principais
tab_colunas, tab_sistema = st.tabs(["📊 Colunas do Relatório", "🔧 Sistema"])

with tab_colunas:
    # Seleção de região e unidade
    col1, col2 = st.columns(2)
    
    with col1:
        regioes = get_regions()
        default_idx = regioes.index(config.get("default_regiao", "SP1")) if config.get("default_regiao", "SP1") in regioes else 0
        regiao = st.selectbox("🌎 Região", options=regioes, index=default_idx, key="cfg_regiao")
    
    with col2:
        unidades = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao)
        unidade = st.selectbox("🏢 Unidade", options=unidades, key="cfg_unidade") if unidades else None
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if not unidade:
        st.info("👆 Selecione uma região e unidade para configurar.")
    else:
        # Definição de colunas
        COLUNAS_PADRAO = [
            ("Unidade", "🏢 Identificação da unidade", True),
            ("Categoria", "📁 Categoria do contrato", True),
            ("Fornecedor", "🏭 Nome do fornecedor", True),
            ("HC Planilha", "👥 Headcount da planilha", True),
            ("Dias Faltas", "📅 Dias de faltas", True),
            ("Horas Atrasos", "⏰ Horas de atrasos", True),
            ("Valor Planilha", "💰 Valor base da planilha", True),
            ("Desc. Falta Validado Atlas", "💸 Desconto de faltas", True),
            ("Desc. Atraso Validado Atlas", "💸 Desconto de atrasos", True),
            ("Desconto SLA Mês", "📊 Desconto SLA do mês", True),
            ("Valor Mensal Final", "💵 Valor final a faturar", True),
            ("Mês de emissão da NF", "📆 Competência da NF", True),
        ]
        
        COLUNAS_EXTRAS = [
            ("Desconto SLA Retroativo", "↩️ Retroativo de SLA", False),
            ("Desconto Equipamentos", "🖥️ Desconto de equipamentos", False),
            ("Prêmio Assiduidade", "🏆 Prêmio por assiduidade", False),
            ("Outros descontos", "📋 Outros descontos", False),
            ("Taxa de prorrogação do prazo pagamento", "📈 Taxa de prorrogação", False),
            ("Valor mensal com prorrogação do prazo pagamento", "💳 Valor com prorrogação", False),
            ("Retroativo de dissídio", "⚖️ Retroativo de dissídio", False),
            ("Parcela (x/x)", "🔢 Parcela", False),
            ("Valor extras validado Atlas", "➕ Extras validados", False),
        ]
        
        # Carregar configuração atual da unidade
        overrides = get_units_overrides()
        unit_cfg = overrides.get(unidade, {})
        colunas_salvas = unit_cfg.get("columns", [col[0] for col in COLUNAS_PADRAO])
        
        col_pad, col_ext = st.columns(2)
        
        with col_pad:
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            ">
                <h3 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1rem;">
                    📋 Colunas Padrão
                </h3>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.8rem; margin: 0.5rem 0 0 0;">
                    Recomendadas para todos os relatórios
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            colunas_selecionadas = []
            for col_name, col_desc, default in COLUNAS_PADRAO:
                checked = col_name in colunas_salvas if colunas_salvas else default
                if st.checkbox(f"{col_desc}", value=checked, key=f"col_{col_name}"):
                    colunas_selecionadas.append(col_name)
        
        with col_ext:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {COLORS['bg_card']} 0%, rgba(139, 92, 246, 0.1) 100%);
                border: 1px solid {COLORS['secondary']};
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            ">
                <h3 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1rem;">
                    ✨ Colunas Extras
                </h3>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.8rem; margin: 0.5rem 0 0 0;">
                    Opcionais - ative conforme necessidade
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            for col_name, col_desc, default in COLUNAS_EXTRAS:
                checked = col_name in colunas_salvas if colunas_salvas else default
                if st.checkbox(f"{col_desc}", value=checked, key=f"col_{col_name}"):
                    colunas_selecionadas.append(col_name)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Mês de referência
        col_mes, col_scope = st.columns(2)
        
        with col_mes:
            mes_atual = unit_cfg.get("month_reference", config.get("default_mes", "2025-10"))
            mes = st.text_input(
                "📅 Mês de Referência",
                value=mes_atual,
                help="Formato: AAAA-MM (ex: 2025-10)"
            )
        
        with col_scope:
            st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
            escopo = st.radio(
                "🎯 Aplicar em:",
                options=[
                    "Somente esta unidade",
                    "Todas as unidades da região",
                    "Todas as unidades (global)",
                ],
                horizontal=True
            )
        
        # Botão salvar
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("💾 SALVAR CONFIGURAÇÕES", use_container_width=True, type="primary"):
                # Validar mês
                if not re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", mes.strip()):
                    st.error("❌ Formato de mês inválido. Use AAAA-MM (ex: 2025-10)")
                else:
                    # Definir alvos
                    if escopo == "Somente esta unidade":
                        targets = [unidade]
                    elif escopo == "Todas as unidades da região":
                        targets = list_units_for_region(config.get("xlsx_dir"), regiao)
                    else:
                        targets = []
                        for r in get_regions():
                            targets.extend(list_units_for_region(config.get("xlsx_dir"), r))
                    
                    # Remover duplicatas
                    targets = list(dict.fromkeys(targets))
                    
                    # Salvar para cada unidade
                    for u in targets:
                        save_unit_override(u, {
                            "columns": colunas_selecionadas,
                            "month_reference": mes.strip()
                        })
                    
                    # Atualizar config global
                    config["default_regiao"] = regiao
                    config["default_mes"] = mes.strip()
                    save_config(config)
                    
                    st.success(f"✅ Configurações salvas para {len(targets)} unidade(s)!")
                    st.balloons()

with tab_sistema:
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0; font-size: 1.1rem;">
            🔧 Configurações do Sistema
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        python_path = st.text_input(
            "🐍 Caminho do Python",
            value=config.get("python_path", "python"),
            help="Caminho do executável Python"
        )
        
        main_py_path = st.text_input(
            "📄 Caminho do main.py",
            value=config.get("main_py_path", "c:/backpperformance/main.py"),
            help="Caminho completo do arquivo main.py"
        )
    
    with col2:
        xlsx_dir = st.text_input(
            "📁 Diretório das Planilhas",
            value=config.get("xlsx_dir", "c:/backpperformance/planilhas"),
            help="Pasta onde estão os arquivos .xlsx"
        )
        
        output_dir = st.text_input(
            "📂 Diretório de Saída",
            value=config.get("output_html_dir", "c:/backpperformance/output_html"),
            help="Pasta onde os HTMLs serão salvos"
        )
    
    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("💾 SALVAR SISTEMA", use_container_width=True):
            config["python_path"] = python_path
            config["main_py_path"] = main_py_path
            config["xlsx_dir"] = xlsx_dir
            config["output_html_dir"] = output_dir
            save_config(config)
            st.success("✅ Configurações do sistema salvas!")
    
    # Info atual
    st.markdown("<hr>", unsafe_allow_html=True)
    
    with st.expander("📋 Configuração Atual (JSON)", expanded=False):
        st.json(config)