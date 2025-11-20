import os
import sys
import warnings
import streamlit as st

# Avisos que não impactam a UI
warnings.filterwarnings("ignore", message=".*Data Validation extension is not supported.*")
warnings.filterwarnings("ignore", message=".*Unknown extension is not supported.*")

# Garantir import do projeto
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

st.set_page_config(page_title="Portal Performance", page_icon="📊", layout="wide")

# Remove a tela/app: redireciona para a primeira página (Execução) para UX mais fluída
try:
    st.switch_page("pages/1_Execução.py")
except Exception:
    # Fallback silencioso se o Streamlit ainda não suportar switch_page no ambiente
    st.markdown("Carregando…")
