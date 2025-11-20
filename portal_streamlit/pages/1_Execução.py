"""
Página de Execução - Portal Performance
"""

import os
import sys
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config, save_config
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles, render_header, COLORS
from portal_streamlit.utils.pipeline import run_pipeline, get_regions, list_units_for_region

# Configuração da página
st.set_page_config(
    page_title="Execução | Portal Performance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos
inject_global_styles()
render_sidebar_branding()

# Header
render_header(
    title="Execução",
    subtitle="Execute a automação de envio de medições",
    icon="⚡"
)

# Carregar configurações
config = get_config()

# Layout principal em cards
col_config, col_actions = st.columns([2, 1])

with col_config:
    # Card de Configuração
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_card']};
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0; font-size: 1.1rem;">
            📋 Configuração do Envio
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Seleção de Região
    regioes = get_regions()
    default_idx = regioes.index(config.get("default_regiao", "SP1")) if config.get("default_regiao", "SP1") in regioes else 0
    
    col1, col2 = st.columns(2)
    with col1:
        regiao = st.selectbox(
            "🌎 Região",
            options=regioes,
            index=default_idx,
            help="Selecione a região para envio"
        )
    
    with col2:
        mes_ref = st.text_input(
            "📅 Mês de Referência",
            value=config.get("default_mes", "2025-10"),
            help="Formato: AAAA-MM"
        )
    
    # Seleção de Unidades
    unidades_da_regiao = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao)
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # Botões de seleção rápida
    col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 2])
    with col_sel1:
        if st.button("✅ Selecionar Todas", use_container_width=True):
            st.session_state['unidades_selecionadas'] = unidades_da_regiao
    with col_sel2:
        if st.button("❌ Limpar Seleção", use_container_width=True):
            st.session_state['unidades_selecionadas'] = []
    
    # Inicializa estado se não existir
    if 'unidades_selecionadas' not in st.session_state:
        st.session_state['unidades_selecionadas'] = unidades_da_regiao
    
    unidades_selecionadas = st.multiselect(
        "🏢 Unidades",
        options=unidades_da_regiao,
        default=st.session_state.get('unidades_selecionadas', unidades_da_regiao),
        help="Selecione as unidades para envio"
    )
    
    # Atualiza estado
    st.session_state['unidades_selecionadas'] = unidades_selecionadas

with col_actions:
    # Card de Ações
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['bg_card']} 0%, {COLORS['bg_dark']} 100%);
        border: 1px solid {COLORS['border']};
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    ">
        <h3 style="color: {COLORS['text_primary']}; margin: 0 0 1rem 0; font-size: 1.1rem;">
            🎯 Modo de Execução
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Toggle de envio real
    envio_real = st.toggle(
        "📤 Envio Real via Outlook",
        value=False,
        help="Quando ativado, os e-mails serão enviados de verdade"
    )
    
    if envio_real:
        st.warning("⚠️ **Atenção:** Os e-mails serão enviados!")
    else:
        st.info("🔒 Modo seguro: apenas preview (dry-run)")
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    permitir_reenvio = st.checkbox(
        "🔄 Permitir Reenvio",
        value=False,
        help="Ignora controle de envio anterior"
    )
    
    # Resumo
    st.markdown(f"""
    <div style="
        background: {COLORS['bg_dark']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
    ">
        <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0;">Resumo:</p>
        <p style="color: {COLORS['text_primary']}; font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
            {len(unidades_selecionadas)} unidade(s)
        </p>
        <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0;">
            Região: {regiao} • Mês: {mes_ref}
        </p>
    </div>
    """, unsafe_allow_html=True)

# Divider
st.markdown("<hr>", unsafe_allow_html=True)

# Botão de Execução
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    executar = st.button(
        "🚀 EXECUTAR AUTOMAÇÃO",
        use_container_width=True,
        type="primary"
    )

# Barra de progresso
progress_container = st.empty()
status_container = st.empty()

# Execução
if executar:
    if not unidades_selecionadas:
        st.error("❌ Selecione pelo menos uma unidade!")
    else:
        cfg = get_config()
        
        with progress_container:
            progress = st.progress(0, text="🔄 Iniciando execução...")
        
        with status_container:
            with st.spinner("Processando..."):
                result = run_pipeline(
                    python_path=cfg.get("python_path", "python"),
                    main_py_path=cfg.get("main_py_path", "c:/backpperformance/main.py"),
                    regiao=regiao,
                    mes=mes_ref,
                    xlsx_dir=cfg.get("xlsx_dir", "c:/backpperformance/planilhas"),
                    dry_run=not envio_real,
                    unidades=unidades_selecionadas,
                    selecionar_colunas=None,
                    portal_overrides_path=None,
                    allow_resend=permitir_reenvio,
                )
        
        progress_container.progress(100, text="✅ Execução concluída!")
        
        # Salvar logs na sessão
        st.session_state["last_stdout"] = result.stdout
        st.session_state["last_stderr"] = result.stderr
        st.session_state["last_returncode"] = result.returncode
        
        if result.returncode == 0:
            if envio_real:
                st.success("✅ **Envio concluído com sucesso!** Os e-mails foram enviados via Outlook.")
            else:
                st.success("✅ **Preview gerado com sucesso!** Acesse a aba Preview para visualizar os HTMLs.")
                st.info("💡 Para enviar os e-mails, ative o toggle 'Envio Real via Outlook' e execute novamente.")
        else:
            st.error(f"❌ **Erro na execução** (código: {result.returncode})")
            st.markdown("Verifique os detalhes abaixo para mais informações.")

# Logs da execução
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

with st.expander("📋 Detalhes da Última Execução", expanded=False):
    tab1, tab2 = st.tabs(["📤 Saída (stdout)", "⚠️ Erros (stderr)"])
    
    with tab1:
        if "last_stdout" in st.session_state and st.session_state["last_stdout"]:
            st.code(st.session_state["last_stdout"], language="text")
        else:
            st.info("Nenhuma saída disponível.")
    
    with tab2:
        if "last_stderr" in st.session_state and st.session_state["last_stderr"]:
            st.code(st.session_state["last_stderr"], language="text")
        else:
            st.info("Nenhum erro registrado.")