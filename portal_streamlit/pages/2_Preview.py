import os, sys, json
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config, get_units_overrides, save_unit_override, get_env_variable
from portal_streamlit.utils.pipeline import (
    get_regions,
    list_units_for_region,
    find_unit_html,
    read_html_file,
    list_output_html_files,
    sanitize_filename_unit,
)
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles

st.set_page_config(page_title="Preview", page_icon="🧐", layout="wide")
inject_global_styles()
render_sidebar_branding()

st.title("Preview")
config = get_config()

regioes = get_regions()
regiao = st.selectbox("Região", options=regioes, index=max(0, regioes.index(config.get("default_regiao", "SP1")) if config.get("default_regiao", "SP1") in regioes else 0))
unidades = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao)
unidade = st.selectbox("Unidade", options=unidades) if unidades else None

if not unidade:
    st.info("Selecione uma região e uma unidade para visualizar o HTML.")
else:
    ym_default = config.get("default_mes", "2025-08")
    output_dir = config.get("output_html_dir", "c:/backpperformance/output_html")

    # Descobre arquivos disponíveis para a unidade e permite escolher o mês
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

    # Se houver arquivos, escolha o mês; senão usaremos um preview mínimo
    if months_found:
        # sugere default se existir, senão o mais recente
        idx = months_found.index(ym_default) if ym_default in months_found else len(months_found) - 1
        ym_sel = st.selectbox("Mês do arquivo (encontrado em output_html)", options=months_found, index=max(0, idx))
        html_path = find_unit_html(output_dir, unidade, ym_sel)
        base_html = read_html_file(html_path) if html_path else read_html_file(unit_files[-1])
    else:
        # Nenhum arquivo encontrado – mostra aviso e usa um HTML mínimo para o preview ao vivo
        st.warning("Nenhum HTML encontrado para esta unidade. Gere a prévia na aba Execução. Mesmo assim, você pode editar os textos abaixo e salvar.")
        base_html = """
        <html><head><meta charset='utf-8'><style>
        body{background:#0f172a;color:#e5e7eb;font-family:Segoe UI,Inter,sans-serif;padding:24px}
        .intro-text{font-size:15px;color:#e5e7eb;line-height:1.7;margin:0 0 16px 0}
        .alert-premium{background:#1f2a44;border:1px solid #2B3B55;border-radius:12px;padding:16px;margin-top:8px}
        .alert-content{color:#e5e7eb}
        </style></head><body>
        <p class='intro-text'><em>Saudação…</em></p>
        <p class='intro-text'>Introdução aqui…</p>
        <div class='alert-premium'><div class='alert-content'><strong>Informação Importante:</strong><br>Observação aqui…</div></div>
        </body></html>
        """

    st.divider()
    st.subheader("Editar introdução e observação (preview em tempo real)")
    overrides = get_units_overrides()
    unit_cfg = overrides.get(unidade, {})

    # Define valores padrão para introdução e observação a partir do .env
    default_intro = get_env_variable("COPY_INTRO", "Bem-vindo(a) à nossa unidade! Aqui você encontrará informações importantes.")
    # Substitui placeholders simples quando aplicável
    if isinstance(default_intro, str) and unidade:
        default_intro = default_intro.replace("{{ unidade }}", unidade)

    default_observation = get_env_variable("COPY_OBSERVATION", "Lembre-se de verificar os detalhes e entrar em contato se precisar de ajuda.")

    # Inicializa os campos com valores salvos ou padrões
    col1, col2 = st.columns(2)
    with col1:
        intro = st.text_area("Introdução", value=unit_cfg.get("intro", default_intro), height=140, key="intro_text")
    with col2:
        observation = st.text_area("Observação", value=unit_cfg.get("observation", default_observation), height=140, key="obs_text")

    # Preview em tempo real: injeta um pequeno script para substituir os trechos no HTML carregado
        js_patch = """
        <script>
        (function() {
            const intro = %INTRO%;
            const obs = %OBS%;
            try {
                const ps = document.querySelectorAll('p.intro-text');
                if (ps && ps.length >= 2) {
                    // ps[0] é a saudação; deixamos como está. ps[1] é a introdução.
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
    st.components.v1.html(live_html, height=700, scrolling=True)

    st.divider()
    col_a, col_b = st.columns([1,3])
    with col_a:
        auto = st.toggle("Salvar automaticamente", value=True, help="Salva as alterações imediatamente ao editar.")
        if st.button("Salvar agora"):
            save_unit_override(unidade, {"intro": intro, "observation": observation})
            st.success("Textos salvos.")
    if 'last_saved' not in st.session_state:
        st.session_state['last_saved'] = {"intro": unit_cfg.get("intro", ""), "observation": unit_cfg.get("observation", "")}
    # Auto-save simples: salva quando mudar e a opção estiver ativada
    if auto:
        if intro != st.session_state['last_saved'].get('intro') or observation != st.session_state['last_saved'].get('observation'):
            save_unit_override(unidade, {"intro": intro, "observation": observation})
            st.session_state['last_saved'] = {"intro": intro, "observation": observation}
            st.toast("Alterações salvas automaticamente.")
