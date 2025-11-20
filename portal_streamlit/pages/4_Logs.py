"""
Página de Logs - Portal Performance
Histórico de execuções e envios
"""

import os
import sys
import sqlite3
import streamlit as st
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles, render_header, render_status_badge, COLORS

# Configuração da página
st.set_page_config(
    page_title="Logs | Portal Performance",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilos
inject_global_styles()
render_sidebar_branding()

# Header
render_header(
    title="Logs",
    subtitle="Histórico de execuções e envios",
    icon="📋"
)

# Caminho do banco
config = get_config()
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "faturamento_logs.db"))

if not os.path.exists(db_path):
    st.warning("⚠️ Banco de logs não encontrado. Ele será criado automaticamente ao executar a automação.")
    st.info("💡 Execute a automação na aba **Execução** para gerar os primeiros registros.")
else:
    try:
        conn = sqlite3.connect(db_path)
        
        # Carregar dados
        try:
            df = pd.read_sql_query(
                "SELECT * FROM send_logs ORDER BY ROWID DESC LIMIT 500", 
                conn
            )
        except Exception:
            df = pd.DataFrame()
        
        conn.close()
        
        if df.empty:
            st.info("📭 Nenhum registro encontrado ainda.")
        else:
            # Métricas resumidas
            col1, col2, col3, col4 = st.columns(4)
            
            total_envios = len(df[df['status'].str.lower().isin(['sent', 'success'])])
            total_dry_run = len(df[df['dry_run'] == 1])
            total_erros = len(df[df['status'].str.lower() == 'failed'])
            unidades_unicas = df['unidade'].nunique()
            
            with col1:
                st.metric("📤 Envios Realizados", total_envios)
            with col2:
                st.metric("🔍 Previews (Dry-run)", total_dry_run)
            with col3:
                st.metric("❌ Erros", total_erros)
            with col4:
                st.metric("🏢 Unidades", unidades_unicas)
            
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Filtros
            st.markdown(f"""
            <div style="
                background: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
                padding: 1rem 1.5rem;
                margin-bottom: 1rem;
            ">
                <h4 style="color: {COLORS['text_primary']}; margin: 0; font-size: 0.95rem;">
                    🔍 Filtros
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            with col_f1:
                regioes_disponiveis = ["(Todas)"] + sorted(df['regiao'].dropna().unique().tolist())
                filtro_regiao = st.selectbox("Região", regioes_disponiveis)
            
            with col_f2:
                unidades_disponiveis = ["(Todas)"] + sorted(df['unidade'].dropna().unique().tolist())
                filtro_unidade = st.selectbox("Unidade", unidades_disponiveis)
            
            with col_f3:
                status_disponiveis = ["(Todos)"] + sorted(df['status'].dropna().unique().tolist())
                filtro_status = st.selectbox("Status", status_disponiveis)
            
            with col_f4:
                tipo_disponiveis = ["(Todos)", "Envio Real", "Dry-run"]
                filtro_tipo = st.selectbox("Tipo", tipo_disponiveis)
            
            # Aplicar filtros
            df_filtrado = df.copy()
            
            if filtro_regiao != "(Todas)":
                df_filtrado = df_filtrado[df_filtrado['regiao'] == filtro_regiao]
            
            if filtro_unidade != "(Todas)":
                df_filtrado = df_filtrado[df_filtrado['unidade'] == filtro_unidade]
            
            if filtro_status != "(Todos)":
                df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]
            
            if filtro_tipo == "Envio Real":
                df_filtrado = df_filtrado[df_filtrado['dry_run'] == 0]
            elif filtro_tipo == "Dry-run":
                df_filtrado = df_filtrado[df_filtrado['dry_run'] == 1]
            
            st.markdown(f"**{len(df_filtrado)}** registro(s) encontrado(s)")
            
            # Tabela de logs
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            
            # Preparar dados para exibição
            df_display = df_filtrado.copy()
            
            # Renomear colunas para exibição
            colunas_exibir = {
                'ts': '📅 Data',
                'regiao': '🌎 Região',
                'unidade': '🏢 Unidade',
                'mes': '📆 Mês',
                'status': '📊 Status',
                'dry_run': '🔍 Tipo',
                'row_count': '📋 Linhas',
                'sum_valor_mensal_final': '💰 Valor Total',
            }
            
            # Selecionar e renomear colunas
            colunas_disponiveis = [c for c in colunas_exibir.keys() if c in df_display.columns]
            df_display = df_display[colunas_disponiveis].copy()
            df_display = df_display.rename(columns={c: colunas_exibir[c] for c in colunas_disponiveis})
            
            # Formatar tipo
            if '🔍 Tipo' in df_display.columns:
                df_display['🔍 Tipo'] = df_display['🔍 Tipo'].apply(
                    lambda x: '🔍 Preview' if x == 1 else '📤 Envio'
                )
            
            # Formatar valor
            if '💰 Valor Total' in df_display.columns:
                df_display['💰 Valor Total'] = df_display['💰 Valor Total'].apply(
                    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(x) else "-"
                )
            
            # Formatar status com cores
            if '📊 Status' in df_display.columns:
                def format_status(s):
                    if pd.isna(s):
                        return "—"
                    s_lower = str(s).lower()
                    if s_lower in ['sent', 'success']:
                        return "✅ Enviado"
                    elif s_lower == 'failed':
                        return "❌ Erro"
                    elif s_lower == 'saved':
                        return "💾 Salvo"
                    elif s_lower == 'resent':
                        return "🔄 Reenviado"
                    return str(s)
                
                df_display['📊 Status'] = df_display['📊 Status'].apply(format_status)
            
            # Exibir tabela
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                height=400
            )
            
            # Detalhes expandíveis
            with st.expander("📋 Ver Detalhes Completos", expanded=False):
                if not df_filtrado.empty:
                    # Selecionar registro
                    idx = st.selectbox(
                        "Selecione um registro:",
                        range(len(df_filtrado)),
                        format_func=lambda i: f"{df_filtrado.iloc[i]['ts']} - {df_filtrado.iloc[i]['unidade']} ({df_filtrado.iloc[i]['status']})"
                    )
                    
                    registro = df_filtrado.iloc[idx]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Informações Gerais:**")
                        st.write(f"- **Data:** {registro.get('ts', '-')}")
                        st.write(f"- **Região:** {registro.get('regiao', '-')}")
                        st.write(f"- **Unidade:** {registro.get('unidade', '-')}")
                        st.write(f"- **Mês:** {registro.get('mes', '-')}")
                        st.write(f"- **Status:** {registro.get('status', '-')}")
                    
                    with col2:
                        st.markdown("**Detalhes do Envio:**")
                        st.write(f"- **Assunto:** {registro.get('subject', '-')}")
                        st.write(f"- **Destinatários:** {registro.get('recipients', '-')}")
                        st.write(f"- **Linhas:** {registro.get('row_count', '-')}")
                        st.write(f"- **Valor Total:** R$ {registro.get('sum_valor_mensal_final', 0):,.2f}")
                    
                    if registro.get('error'):
                        st.error(f"**Erro:** {registro.get('error')}")
            
            # Botão de exportar
            st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                csv = df_filtrado.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Exportar CSV",
                    csv,
                    "logs_portal_performance.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                if st.button("🔄 Atualizar", use_container_width=True):
                    st.rerun()
                    
    except Exception as e:
        st.error(f"❌ Erro ao ler banco de dados: {e}")