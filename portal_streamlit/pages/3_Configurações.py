import os, sys
import streamlit as st

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from portal_streamlit.utils.config_manager import get_config, save_config, get_units_overrides, save_unit_override
from portal_streamlit.utils.pipeline import get_regions, list_units_for_region
from portal_streamlit.utils.pipeline import REGIOES  # para labels
from portal_streamlit.utils.ui import render_sidebar_branding, inject_global_styles

st.set_page_config(page_title="Configurações", page_icon="🛠️", layout="wide")
inject_global_styles()
render_sidebar_branding()

st.title("Configurações")
config = get_config()

# Região e unidade
regioes = get_regions()
regiao = st.selectbox("Região", options=regioes, index=max(0, regioes.index(config.get("default_regiao", "SP1")) if config.get("default_regiao", "SP1") in regioes else 0))
unidades = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao)
unidade = st.selectbox("Unidade", options=unidades) if unidades else None

st.divider()
st.subheader("Colunas do relatório")

DEFAULTS = [
    "Unidade", "Categoria", "Fornecedor", "HC Planilha", "Dias Faltas", "Horas Atrasos",
    "Valor Planilha", "Desc. Falta Validado Atlas", "Desc. Atraso Validado Atlas", "Desconto SLA Mês",
    "Valor Mensal Final", "Mês de emissão da NF"
]
EXTRAS = [
    "Desconto SLA Retroativo", "Desconto Equipamentos", "Prêmio Assiduidade", "Outros descontos",
    "Taxa de prorrogação do prazo pagamento", "Valor mensal com prorrogação do prazo pagamento",
    "Retroativo de dissídio", "Parcela (x/x)", "Valor extras validado Atlas"
]

if unidade:
    st.caption("Marque/desmarque as colunas para esta unidade.")
    # Aqui poderíamos carregar preferências por unidade, por enquanto usamos defaults todos marcados; extras desmarcados
    st.write("Padrão (sempre recomendadas):")
    default_flags = {c: st.checkbox(c, value=True, key=f"def_{c}") for c in DEFAULTS}
    st.write("Extras (opcionais):")
    # por padrão, extras desmarcados (inclui 'Desconto SLA Retroativo')
    extra_flags = {c: st.checkbox(c, value=False, key=f"ext_{c}") for c in EXTRAS}
    selecionadas = [c for c, v in {**default_flags, **extra_flags}.items() if v]

    st.divider()
    st.subheader("Data de emissão da NF (mês de referência)")
    mes = st.text_input("Mês (AAAA-MM)", value=config.get("default_mes", "2025-08"), help="Formato: 2025-08")

    st.divider()
    st.subheader("Aplicação das preferências")
    apply_scope = st.radio(
        "Aplicar estas preferências em:",
        options=[
            "Somente esta unidade",
            "Todas as unidades desta região",
            "Todas as unidades (todas as regiões)",
        ],
        index=0,
        help="Escolha onde as seleções de colunas e o mês de referência serão aplicados.",
    )

    if st.button("Salvar preferências"):
        config["default_regiao"] = regiao
        # validação mínima AAAA-MM
        import re
        m = re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", str(mes).strip())
        if m:
            config["default_mes"] = mes.strip()
        else:
            st.warning("Mês inválido. Use o formato AAAA-MM.")

        # Define alvo conforme escopo
        targets = []
        if apply_scope == "Somente esta unidade":
            targets = [unidade]
        elif apply_scope == "Todas as unidades desta região":
            targets = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), regiao) or []
        else:  # Todas as unidades (todas as regiões)
            targets = []
            for r in get_regions():
                units_r = list_units_for_region(config.get("xlsx_dir", "c:/backpperformance/planilhas"), r) or []
                targets.extend(units_r)

        # Remover duplicadas preservando ordem
        seen = set()
        unique_targets = []
        for u in targets:
            if u not in seen:
                unique_targets.append(u)
                seen.add(u)

        # Guardar preferências de colunas + mês para cada unidade alvo
        month_value = mes.strip() if m else config.get("default_mes", "2025-08")
        for u in unique_targets:
            save_unit_override(u, {"columns": selecionadas, "month_reference": month_value})

        save_config(config)

        if len(unique_targets) == 1:
            st.success("Preferências salvas para a unidade.")
        else:
            st.success(f"Preferências aplicadas em {len(unique_targets)} unidades.")
else:
    st.info("Selecione uma região e uma unidade.")
