"""
Página de Preview - Portal Performance
Visualização e edição dos e-mails gerados
"""

import os
import sys
import json
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import (
    get_config, get_units_overrides, save_unit_override, get_env_variable
)
from portal_streamlit.utils.pipeline import (
    get_regions, list_units_for_region, find_unit_html,
    read_html_file, list_output_html_files, sanitize_filename_unit
)
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles, render_header, COLORS

# Configuração da página
st.set_page_config(
    page_title="Preview | Portal Performance",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos
inject_global_styles()
render_sidebar_branding()

# Header
render_header(
    title="Preview",
    subtitle="Visualize e edite os e-mails antes do envio",
    icon="👁️"
)

# Carregar configurações
config = get_config()

# Seleção de região e unidade
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    regioes = get_regions()
    default_idx = regioes.index(config.get("default_regiao", "SP1")) if config.get("default_regiao", "SP1") in regioes else 0
    regiao = st.selectbox("🌎 Região", options=regioes, index=default_idx)

with col2:
    unidades = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao)
    unidade = st.selectbox("🏢 Unidade", options=unidades) if unidades else None

with col3:
    if unidade:
        output_dir = config.get("output_html_dir", "c:/backpperformance/output_html")
        files_all = list_output_html_files(output_dir)
        base_name = sanitize_filename_unit(unidade)
        unit_files = [f for f in files_all if os.path.basename(f).startswith(base_name + "_")]
        
        months_found = []
        for f in unit_files:
            name = os.path.basename(f)
            try:
                m = name.split("_")[-1].replace(".html", "").strip()
                months_found.append(m)
            except Exception:
                pass
        months_found = sorted(set(months_found))
        
        if months_found:
            ym_default = config.get("default_mes", "2025-10")
            idx = months_found.index(ym_default) if ym_default in months_found else len(months_found) - 1
            ym_sel = st.selectbox("📅 Mês", options=months_found, index=max(0, idx))
        else:
            ym_sel = None
            st.warning("Nenhum arquivo encontrado")
    else:
        ym_sel = None

st.markdown("<hr>", unsafe_allow_html=True)

if not unidade:
    st.info("👆 Selecione uma região e unidade para visualizar o preview.")
else:
    # Carregar HTML
    output_dir = config.get("output_html_dir", "c:/backpperformance/output_html")
    
    if ym_sel:
        html_path = find_unit_html(output_dir, unidade, ym_sel)
        base_html = read_html_file(html_path) if html_path else ""
    else:
        base_html = ""
    
    if not base_html:
        st.warning("⚠️ Nenhum HTML encontrado. Execute a automação na aba **Execução** primeiro.")
        base_html = f"""
        <html><head><meta charset='utf-8'><style>
        body{{background:#0f172a;color:#e5e7eb;font-family:Inter,sans-serif;padding:40px;text-align:center}}
        .placeholder{{background:#1e293b;border:2px dashed #334155;border-radius:16px;padding:60px 40px;margin-top:40px}}
        h2{{color:#94a3b8;font-weight:600}}
        p{{color:#64748b}}
        </style></head><body>
        <div class="placeholder">
            <h2>📧 Preview do E-mail</h2>
            <p>Execute a automação para gerar o preview de <strong>{unidade}</strong></p>
        </div>
        </body></html>
        """
    
    # Layout: Editor + Preview
    col_edit, col_preview = st.columns([1, 2])
    
    with col_edit:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1.1rem;">
                ✏️ Editor de Textos
            </h3>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                Personalize os textos do e-mail
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Carregar overrides existentes
        overrides = get_units_overrides()
        unit_cfg = overrides.get(unidade, {})
        
        # Defaults do .env
        default_intro = get_env_variable("COPY_INTRO", "Encaminhamos a medição mensal...")
        if isinstance(default_intro, str) and unidade:
            default_intro = default_intro.replace("{{ unidade }}", unidade)
        default_observation = get_env_variable("COPY_OBSERVATION", "Observação: caso a Nota Fiscal...")
        
        # Campos de edição
        intro = st.text_area(
            "📝 Introdução",
            value=unit_cfg.get("intro", default_intro),
            height=150,
            key="intro_text",
            help="Texto de abertura do e-mail"
        )
        
        observation = st.text_area(
            "⚠️ Observação",
            value=unit_cfg.get("observation", default_observation),
            height=120,
            key="obs_text",
            help="Texto da caixa de observação"
        )
        
        # Opções de salvamento
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        
        auto_save = st.toggle("💾 Salvar automaticamente", value=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("💾 Salvar", use_container_width=True):
                save_unit_override(unidade, {"intro": intro, "observation": observation})
                st.success("✅ Salvo!")
        
        with col_btn2:
            if st.button("🔄 Restaurar Padrão", use_container_width=True):
                save_unit_override(unidade, {"intro": default_intro, "observation": default_observation})
                st.rerun()
        
        # Auto-save
        if auto_save:
            if 'last_saved' not in st.session_state:
                st.session_state['last_saved'] = {"intro": unit_cfg.get("intro", ""), "observation": unit_cfg.get("observation", "")}
            
            if intro != st.session_state['last_saved'].get('intro') or observation != st.session_state['last_saved'].get('observation'):
                save_unit_override(unidade, {"intro": intro, "observation": observation})
                st.session_state['last_saved'] = {"intro": intro, "observation": observation}
                st.toast("💾 Salvo automaticamente!")
    
    with col_preview:
        st.markdown(f"""
        <div style="
            background: {COLORS['bg_card']};
            border: 1px solid {COLORS['border']};
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        ">
            <h3 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1.1rem;">
                👁️ Preview em Tempo Real
            </h3>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 0.5rem 0 0 0;">
                Visualização do e-mail que será enviado
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Injetar JS para atualizar preview em tempo real
        js_patch = """
        <script>
        (function() {
            const intro = %INTRO%;
            const obs = %OBS%;
            try {
                const ps = document.querySelectorAll('p.intro-text');
                if (ps && ps.length >= 2) {
                    ps[1].innerHTML = intro;
                }
                const ac = document.querySelector('.alert-premium .alert-content');
                if (ac) {
                    const strong = ac.querySelector('strong');
                    if (strong) {
                        const prefix = strong.outerHTML + '<br>';
                        ac.innerHTML = prefix + obs;
                    } else {
                        ac.innerHTML = obs;
                    }
                }
            } catch (e) { /* ignore */ }
        })();
        </script>
        """.replace("%INTRO%", json.dumps(intro)).replace("%OBS%", json.dumps(observation))
        
        live_html = base_html + "\n" + js_patch
        
        # Container do preview
        st.components.v1.html(live_html, height=700, scrolling=True)

# Dicas
with st.expander("💡 Dicas de Uso", expanded=False):
    st.markdown(f"""
    <div style="color: {COLORS['text_secondary']}; line-height: 1.8;">
    
    **Como usar o Preview:**
    
    1. **Selecione** a região, unidade e mês desejados
    2. **Edite** os textos de introdução e observação no painel esquerdo
    3. **Visualize** as alterações em tempo real no painel direito
    4. As alterações são **salvas automaticamente** (ou clique em "Salvar")
    
    **Variáveis disponíveis:**
    - `{{{{ unidade }}}}` - Nome da unidade
    - `{{{{ mes_extenso }}}}` - Mês por extenso (ex: "Outubro/2025")
    - `{{{{ regiao }}}}` - Código da região
    
    **HTML permitido:**
    - `<strong>texto</strong>` - Negrito
    - `<em>texto</em>` - Itálico
    - `<br>` - Quebra de linha
    
    </div>
    """, unsafe_allow_html=True)