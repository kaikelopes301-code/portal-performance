import os
import streamlit as st

def render_sidebar_branding(title: str = "Portal Performance", subtitle: str = "Operação e revisão dos relatórios HTML"):
	"""Renderiza logo + título + navegação na sidebar de forma consistente.

	Não altera funcionalidades, apenas visual.
	"""
	logo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo-atlas.png"))
	with st.sidebar:
		try:
			st.image(logo_path, use_container_width=True)
		except Exception:
			pass
		st.markdown(f"<div style='margin-top: -0.5rem; font-size: 1.3rem; font-weight: 700;'> {title}</div>", unsafe_allow_html=True)
		if subtitle:
			st.caption(subtitle)
		st.divider()
		st.page_link("pages/1_Execução.py", label="Execução")
		st.page_link("pages/2_Preview.py", label="Preview")
		st.page_link("pages/3_Configurações.py", label="Configurações")
		st.page_link("pages/4_Logs.py", label="Logs")
		st.page_link("pages/5_Ajuda.py", label="Ajuda")


def inject_global_styles():
	"""Aplica pequenos ajustes visuais globais para melhor UX.

	Mantém layout padrão do Streamlit, com refinamentos sutis.
	"""
	st.markdown(
		"""
		<style>
		/* Esconde navegação padrão para evitar duplicação e permitir branding no topo */
		section[data-testid="stSidebarNav"],
		div[data-testid="stSidebarNav"],
		nav[data-testid="stSidebarNav"] {
			display: none !important;
		}

		/* Títulos mais harmoniosos */
		h1, .stMarkdown h1 { font-size: 1.8rem; margin-bottom: 0.5rem; }
		h2, .stMarkdown h2 { font-size: 1.4rem; margin-top: 0.8rem; }

		/* Inputs com leve sombra para profundidade */
		.stTextInput input,
		.stSelectbox [role="combobox"],
		.stMultiSelect [role="combobox"],
		textarea { box-shadow: 0 1px 3px rgba(0,0,0,0.06); }

		/* Botões mais proeminentes (pill) */
		.stButton > button { font-weight: 600; border-radius: 100px; }

		/* Dataframe com linhas zebras sutis */
		.stDataFrame table tbody tr:nth-child(odd) { background: rgba(0,0,0,0.02); }
		</style>
		""",
		unsafe_allow_html=True,
	)
