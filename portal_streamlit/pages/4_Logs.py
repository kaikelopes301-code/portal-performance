import os
import sqlite3
import sys
import streamlit as st
import pandas as pd
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config

st.set_page_config(page_title="Logs", page_icon="📒", layout="wide")
inject_global_styles()
render_sidebar_branding()

st.title("Logs")
config = get_config()

db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "faturamento_logs.db"))

if not os.path.exists(db_path):
    st.warning("Banco de logs não encontrado. Ele é criado ao rodar o pipeline.")
else:
    try:
        conn = sqlite3.connect(db_path)
        dfs = {}
        try:
            tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn)
        except Exception:
            tables = pd.DataFrame({"name": []})
        table_names = tables['name'].tolist()

        # Se existir tabela de logs principal, usa ela; senão, mostra a primeira
        preferred = 'logs'
        table = st.selectbox("Tabela", options=table_names, index=max(0, table_names.index(preferred)) if preferred in table_names else 0) if table_names else None
        if not table:
            st.info("Sem tabelas no banco de dados.")
        else:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table} ORDER BY ROWID DESC LIMIT 500", conn)
            except Exception:
                df = pd.DataFrame()
            # Filtros
            col1, col2, col3 = st.columns(3)
            with col1:
                regiao = st.selectbox("Região", options=["(todas)"] + sorted(df['regiao'].dropna().unique().tolist())) if 'regiao' in df.columns else "(todas)"
            with col2:
                unidade = st.selectbox("Unidade", options=["(todas)"] + sorted(df['unidade'].dropna().unique().tolist())) if 'unidade' in df.columns else "(todas)"
            with col3:
                status = st.selectbox("Status", options=["(todos)"] + sorted(df['status'].dropna().unique().tolist())) if 'status' in df.columns else "(todos)"

            fdf = df.copy()
            if 'regiao' in fdf.columns and regiao != "(todas)":
                fdf = fdf[fdf['regiao'] == regiao]
            if 'unidade' in fdf.columns and unidade != "(todas)":
                fdf = fdf[fdf['unidade'] == unidade]
            if 'status' in fdf.columns and status != "(todos)":
                fdf = fdf[fdf['status'] == status]

            # esconder colunas muito verbosas por padrão
            hide_cols = [c for c in ["subject","recipients","workbook_path","html_path","error","visible_columns"] if c in fdf.columns]
            st.dataframe(fdf, use_container_width=True, hide_index=True, column_config={c: st.column_config.Column(label=c, visible=False) for c in hide_cols})
    except Exception as e:
        st.error(f"Erro ao ler DB: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
