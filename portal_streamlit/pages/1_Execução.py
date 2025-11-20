import os, sys
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config, save_config
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles
from portal_streamlit.utils.pipeline import run_pipeline

st.set_page_config(page_title="Execução", page_icon="⚙️", layout="wide")
inject_global_styles()
render_sidebar_branding()

st.title("Execução")
config = get_config()

from portal_streamlit.utils.pipeline import get_regions, list_units_for_region

regioes = get_regions()
regiao = st.selectbox("Região", options=regioes, index=max(0, regioes.index(config.get("default_regiao", "SP1")) if config.get("default_regiao", "SP1") in regioes else 0))

unidades_da_regiao = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao)
unidades_selecionadas = st.multiselect("Unidades", options=unidades_da_regiao, default=unidades_da_regiao)

envio_real = st.toggle("Envio real via Outlook", value=False, help="Desmarca o dry-run e envia os e-mails usando o Outlook instalado no Windows.")
permitir_reenvio = st.checkbox("Permitir reenvio (ignorar controle de envio anterior)", value=False)
st.caption("Quando o envio real estiver desligado, geramos apenas os HTMLs (dry-run).")

exec_col1, exec_col2 = st.columns([1,2])
with exec_col1:
    iniciar = st.button("Executar")
with exec_col2:
    progress = st.progress(0, text="Aguardando execução…")

if iniciar:
    cfg = get_config()
    total = max(1, len(unidades_selecionadas))
    done = 0
    # Executa por região com filtro de unidades
    result = run_pipeline(
        python_path=cfg.get("python_path", "python"),
        main_py_path=cfg.get("main_py_path", "c:/backpperformance/main.py"),
        regiao=regiao,
        mes=cfg.get("default_mes", "2025-08"),  # vem das configurações
        xlsx_dir=cfg.get("xlsx_dir", "c:/backpperformance/planilhas"),
        dry_run=not envio_real,
        unidades=unidades_selecionadas,
        selecionar_colunas=None,
        portal_overrides_path=None,
        allow_resend=permitir_reenvio,
    )
    done = total
    progress.progress(int(done/total*100), text="Concluído")
    st.session_state["last_stdout"] = result.stdout
    st.session_state["last_stderr"] = result.stderr
    if result.returncode == 0:
        if envio_real:
            st.success("Envio real concluído via Outlook. Consulte a aba Logs para verificar os registros.")
        else:
            st.success("Execução concluída (dry-run). Veja a aba Preview para visualizar os HTMLs.")
    else:
        st.error(f"Falha na execução (code {result.returncode}). Veja logs abaixo.")

st.divider()
with st.expander("Detalhes da última execução (stdout/stderr)", expanded=False):
    if "last_stdout" in st.session_state:
        st.code(st.session_state["last_stdout"], language="text")
    if "last_stderr" in st.session_state:
        st.code(st.session_state["last_stderr"], language="text")
