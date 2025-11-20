import argparse
import json
import sys
import webbrowser
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
import unicodedata
import re  # fallback de coluna

from config_loader import load_overrides, resolve_overrides, ResolvedConfig, OverrideConfigError
from extractor import Extractor
from processor import DEFAULT_DISPLAY_COLUMNS, filter_and_prepare, map_columns
from emailer import Emailer
from utils import (
    previous_month_from_today,
    load_env,
    ensure_sqlite,
    log_sqlite,
    normalize_unit,
    parse_year_month,
    configure_utf8_stdio,
    has_successful_send,
    safe_write_text,
    safe_parse_json,
)

COPY_PROMPTS = [
    ("greeting", "COPY_GREETING", "Saudacao"),
    ("intro", "COPY_INTRO", "Introducao"),
    ("observation", "COPY_OBSERVATION", "Observacao"),
    ("cta_label", "COPY_CTA_LABEL", "Rotulo do botao"),
    ("footer_signature", "COPY_FOOTER_SIGNATURE", "Rodape/assinatura"),
]

def resolve_auto_month(env_cfg: Dict[str, str], unidade: Optional[str]) -> str:
    raw = env_cfg.get("UNIT_EXCEPTIONS", "").strip()
    try:
        exceptions = safe_parse_json(raw) if raw else {}
        if not isinstance(exceptions, dict):
            exceptions = {}
    except Exception:
        exceptions = {}
    if unidade and unidade in exceptions:
        parsed = parse_year_month(exceptions[unidade])
        if parsed:
            return parsed
    mode = (env_cfg.get("DEFAULT_REF_MODE", "previous_month") or "previous_month").lower()
    if mode == "fixed":
        fixed = env_cfg.get("FIXED_REF_YEAR_MONTH", "")
        parsed = parse_year_month(fixed)
        if parsed:
            return parsed
    return previous_month_from_today()

def pick_workbook(xlsx_dir: Path, regiao: str, extractor: Extractor) -> Path:
    workbook = extractor.find_workbook(regiao)
    if not workbook or not workbook.exists():
        raise FileNotFoundError(f"Planilha nao encontrada para a regiao '{regiao}' em {xlsx_dir}.")
    return workbook

def save_html(output_dir: Path, unidade: str, ym: str, html: str) -> Path:
    sanitized = "".join(ch for ch in unidade if ch.isalnum() or ch in {"_", "-", " "}).strip().replace(" ", "_")
    output = output_dir / f"{sanitized}_{ym}.html"
    safe_write_text(output, html)
    return output

def _normalize_generic(value: str) -> str:
    if value is None:
        return ""
    lowered = str(value).strip().lower()
    normalized = "".join(ch for ch in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(ch))
    return " ".join(normalized.split())

def prompt_select_from_list(options: List[str], label: str) -> List[str]:
    if not options:
        return []

    print()
    print(label)
    for idx, option in enumerate(options, 1):
        print(f"{idx}) {option}")

    try:
        raw = input("Digite os numeros desejados (separe por virgula, ponto e virgula ou espaco; Enter para PADRÃO): ").strip()
    except EOFError:
        return []

    if not raw:
        return []

    sanitized = raw.replace(";", " ").replace(",", " ")
    tokens = [token for token in sanitized.split() if token]
    selected: List[str] = []
    normalized_map = {_normalize_generic(opt): opt for opt in options}

    for token in tokens:
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(options):
                value = options[idx]
                if value not in selected:
                    selected.append(value)
            else:
                print(f"[WARN] Indice '{token}' fora do intervalo; ignorando.")
        else:
            normalized = _normalize_generic(token)
            matched = normalized_map.get(normalized)
            if matched and matched not in selected:
                selected.append(matched)
            else:
                print(f"[WARN] Entrada '{token}' nao reconhecida; ignorando.")

    return selected

def get_user_overrides(env_cfg: Dict[str, str], available_columns: List[str], available_units: List[str]) -> Dict[str, Any]:
    overrides = {"copy_overrides": {}, "selected_columns": [], "selected_units": []}

    if not sys.stdin.isatty():
        return overrides

    print()
    try:
        wants_copy = input("Deseja sobrescrever os textos padrao? (s/N): ").strip().lower()
    except EOFError:
        return overrides

    if wants_copy in {"s", "sim", "y", "yes"}:
        for key, env_key, label in COPY_PROMPTS:
            current = env_cfg.get(env_key) or Emailer.COPY_DEFAULTS.get(key, "")
            print(f"\n{label} atual:\n{current}")
            try:
                new_value = input("Digite novo texto (Enter para manter): ").strip()
            except EOFError:
                new_value = ""
            if new_value:
                overrides["copy_overrides"][key] = new_value

    if available_columns:
        selected_columns = prompt_select_from_list(
            available_columns,
            "Selecione colunas para o relatorio (digite numeros; Enter para PADRÃO — só as colunas fixas):",
        )
        if selected_columns:
            overrides["selected_columns"] = selected_columns

    if available_units:
        selected_units = prompt_select_from_list(
            available_units,
            "Selecione unidades (digite numeros separados por virgula, ponto e virgula ou espaco; Enter para todas):",
        )
        if selected_units:
            overrides["selected_units"] = selected_units

    return overrides

def collect_units(df, unit_col: str) -> Dict[str, str]:
    INVALID_MARKERS = {
        "", "-", "nan", "na", "n/a",
        "preenchimento pendente", "pendente", "nao informado", "não informado",
    }
    mapping: Dict[str, str] = {}
    for value in df[unit_col].dropna():
        raw = str(value).strip()
        lowered = raw.lower()
        normalized = "".join(ch for ch in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(ch))
        normalized = " ".join(normalized.split())
        if normalized in INVALID_MARKERS:
            continue
        nu = normalize_unit(raw)
        if nu and nu not in mapping:
            mapping[nu] = raw
    return mapping

def _debug_print_columns(requested: List[str], processed: List[str], html_cols: List[str]) -> None:
    def _join(xs: List[str]) -> str:
        return ", ".join(xs) if xs else "(nenhuma)"
    extras_catalog = list(Emailer.EXTRA_AFTER_SLA) + list(Emailer.GROUP_AFTER_VALOR_MENSAL)
    extras_selected = [c for c in requested if c in extras_catalog]
    print("\n[DEBUG] Colunas (dry-run)")
    print("  - Solicitadas (input):            ", _join(requested))
    print("  - Extras selecionados (9 novas):  ", _join(extras_selected))
    print("  - Processadas (processor):        ", _join(processed))
    print("  - Enviadas ao HTML:               ", _join(html_cols))
    print()

def main() -> None:
    configure_utf8_stdio()

    parser = argparse.ArgumentParser(description="Automacao de envio de e-mails de faturamento mensal por unidade/regiao.")
    parser.add_argument("--regiao", required=True, choices=["RJ", "SP1", "SP2", "SP3", "NNE"], help="Regiao (ex.: RJ, SP1, SP2, SP3, NNE)")
    parser.add_argument("--unidade", required=False, help="Nome exato da unidade (se omitido, processa todas as unidades da regiao)")
    parser.add_argument("--mes", required=False, help="Mes de emissao da NF no formato YYYY-MM")
    parser.add_argument("--force-mes", required=False, help="Forca o mes de referencia para todas as unidades (YYYY-MM)")
    parser.add_argument("--overrides-path", required=False, help="Caminho para o arquivo JSON de overrides")
    parser.add_argument("--dry-run", action="store_true", help="Gera HTMLs localmente sem enviar e-mails")
    parser.add_argument("--xlsx-dir", default=".", help="Diretorio onde estao as planilhas .xlsx")
    parser.add_argument("--preview", action="store_true", help="Abre o HTML gerado no navegador")
    parser.add_argument("--list-cols", action="store_true", help="Lista as colunas detectadas na planilha da regiao e sai")
    parser.add_argument("--non-interactive", action="store_true", help="Forca modo nao interativo (ignora prompts)")
    parser.add_argument("--allow-resend", action="store_true", help="Permite reenvio mesmo se ja houver registro de envio anterior")
    # Integração com o portal (execução não interativa)
    parser.add_argument("--units", required=False, help="Lista de unidades separadas por virgula (ignora menu interativo)")
    parser.add_argument("--columns", required=False, help="Lista de colunas separadas por virgula (ignora menu interativo)")
    parser.add_argument("--portal-overrides-path", required=False, help="Caminho para overrides do portal (JSON por unidade)")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    env_cfg = load_env(project_root / ".env")

    templates_dir = project_root / "templates"
    assets_dir = project_root / "assets"
    output_dir = project_root / "output_html"
    db_path = project_root / "faturamento_logs.db"
    ensure_sqlite(db_path)

    cli_mes: Optional[str] = None
    if args.mes:
        cli_mes = parse_year_month(args.mes)
        if not cli_mes:
            print(f"[ERROR] --mes deve estar no formato YYYY-MM. Recebido: {args.mes}")
            sys.exit(1)

    force_mes: Optional[str] = None
    if args.force_mes:
        force_mes = parse_year_month(args.force_mes)
        if not force_mes:
            print(f"[ERROR] --force-mes deve estar no formato YYYY-MM. Recebido: {args.force_mes}")
            sys.exit(1)

    try:
        overrides_data = load_overrides(
            args.overrides_path,
            base_dir=project_root,
            env_json=env_cfg.get("UNIT_OVERRIDES_JSON"),
        )
    except (FileNotFoundError, OverrideConfigError) as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    source_label = overrides_data.get("__source__") or ""
    print(f"[INFO] Overrides carregados de: {source_label}" if source_label else "[INFO] Overrides nao informados; utilizando comportamento padrao.")

    extractor = Extractor(Path(args.xlsx_dir))
    emailer = Emailer(templates_dir, assets_dir, env_cfg)

    workbook = pick_workbook(Path(args.xlsx_dir), args.regiao, extractor)
    print(f"[INFO] Planilha: {workbook}")
    df, sheet_name = extractor.read_region_sheet(workbook, args.regiao)

    mapping = map_columns(df)
    unit_col = mapping.get("Unidade")
    mes_col = mapping.get("Mes_Emissão_NF")

    # --- Fallback robusto para "Mês de emissão da NF" ---
    MES_EMISSAO_ALIASES = [
        "mes de emissao da nf", "mês de emissão da nf",
        "mes emissao nf", "mes de emissao nf",
        "mes emissao da nota", "mes de emissao da nota",
        "mes de emissao da nota fiscal", "mes emissao nota fiscal",
        "mes nf", "mês nf",
    ]

    def _is_mes_emissao_col(name: str) -> bool:
        n = _normalize_generic(name)
        if any(alias in n for alias in MES_EMISSAO_ALIASES):
            return True
        return (
            re.search(r"\bmes\b.*\bemissao\b.*\b(nf|nota)\b", n) is not None
            or re.search(r"\b(nf|nota)\b.*\bemissao\b.*\bmes\b", n) is not None
        )

    if not mes_col or mes_col not in df.columns:
        candidates = [c for c in df.columns if _is_mes_emissao_col(str(c))]
        if candidates:
            mes_col = candidates[0]
            mapping["Mes_Emissão_NF"] = mes_col
            print(f"[INFO] Coluna 'Mês de emissão da NF' detectada automaticamente: '{mes_col}'")
    # -----------------------------------------------------

    if not unit_col or unit_col not in df.columns:
        raise RuntimeError("Coluna de unidade nao encontrada na planilha.")
    if not mes_col or mes_col not in df.columns:
        raise RuntimeError("Coluna de mes de emissão da NF nao encontrada na planilha.")

    unit_map = collect_units(df, unit_col)
    available_units = list(unit_map.values())

    # ==== MENU DE COLUNAS (padrão + extras) ====
    available_columns = list(DEFAULT_DISPLAY_COLUMNS) \
        + Emailer.EXTRA_AFTER_SLA \
        + Emailer.EXTRA_AFTER_FINAL \
        + Emailer.EXTRA_EXTRAS

    overrides_cli = {"copy_overrides": {}, "selected_columns": [], "selected_units": []}
    if not args.non_interactive and sys.stdin.isatty():
        overrides_cli = get_user_overrides(
            env_cfg,
            available_columns,
            available_units,
        )
    copy_overrides_cli = overrides_cli["copy_overrides"]
    selected_columns_cli = overrides_cli["selected_columns"]
    selected_units_cli = overrides_cli["selected_units"]

    # --- Flags não interativas vindas do portal ---
    # Colunas
    if args.columns:
        toks = [t.strip() for t in args.columns.replace(";", ",").split(",") if t.strip()]
        if toks:
            selected_columns_cli = toks
    # Unidades
    units_flag: Optional[List[str]] = None
    if args.units:
        units_flag = [t.strip() for t in args.units.replace(";", ",").split(",") if t.strip()]

    INVALID_MARKERS = {
        "", "-", "nan", "na", "n/a",
        "preenchimento pendente", "pendente", "nao informado", "não informado",
    }

    if args.unidade:
        norm_requested = normalize_unit(args.unidade)
        unidade_escolhida = unit_map.get(norm_requested)
        if not unidade_escolhida:
            raise RuntimeError(f"Unidade '{args.unidade}' nao encontrada na planilha.")
        unidades = [unidade_escolhida]
    else:
        unidades = list(unit_map.values())
        # prioridade: --units > seleção interativa
        if units_flag:
            filtered: List[str] = []
            for candidate in units_flag:
                if candidate.strip().lower() in INVALID_MARKERS:
                    continue
                real = unit_map.get(normalize_unit(candidate))
                if real:
                    filtered.append(real)
                else:
                    print(f"[WARN] Unidade '{candidate}' nao encontrada; ignorando.")
            if filtered:
                unidades = filtered
        elif selected_units_cli:
            filtered: List[str] = []
            for candidate in selected_units_cli:
                real = unit_map.get(normalize_unit(candidate))
                if real:
                    filtered.append(real)
                else:
                    print(f"[WARN] Unidade '{candidate}' nao encontrada; ignorando.")
            if filtered:
                unidades = filtered

    if not unidades:
        print("[WARN] Nenhuma unidade encontrada para processamento.")
        return

    fallback_email = env_cfg.get("FALLBACK_EMAIL", "").strip()

    total_processed = 0
    errors = 0

    # Carrega overrides do portal (texto por unidade)
    portal_overrides: Dict[str, Any] = {}
    # default: procurar no diretório do portal
    default_portal_path = project_root / "portal_streamlit" / "data" / "overrides.json"
    portal_path = None
    if args.portal_overrides_path:
        portal_path = Path(args.portal_overrides_path)
    elif default_portal_path.exists():
        portal_path = default_portal_path
    if portal_path and portal_path.exists():
        try:
            with open(portal_path, "r", encoding="utf-8") as f:
                portal_overrides = json.load(f) or {}
            print(f"[INFO] Portal overrides: {portal_path}")
        except Exception as e:
            print(f"[WARN] Nao foi possivel ler portal overrides ({portal_path}): {e}")

    # normaliza chaves de unidade do portal para matching robusto
    portal_overrides_norm: Dict[str, Any] = {}
    for k, v in (portal_overrides or {}).items():
        nk = normalize_unit(k)
        if nk and nk not in portal_overrides_norm:
            portal_overrides_norm[nk] = v

    for unidade in unidades:
        resolved: Optional[ResolvedConfig] = None
        summary: Optional[Dict[str, Any]] = None
        try:
            auto_mes = resolve_auto_month(env_cfg, unidade)
            # Preferência do portal: mês individual por unidade
            nu_portal = normalize_unit(unidade)
            portal_unit_pref = portal_overrides_norm.get(nu_portal) if nu_portal else None
            force_mes_unit = None
            if isinstance(portal_unit_pref, dict):
                raw_m = str(portal_unit_pref.get("month_reference", "")).strip()
                if raw_m:
                    pm = parse_year_month(raw_m)
                    if pm:
                        force_mes_unit = pm
            resolved = resolve_overrides(
                args.regiao,
                unidade,
                cli_mes,
                force_mes_unit or force_mes,
                auto_mes=auto_mes,
            )
            print(f"[INFO] {unidade}: mes de referencia {resolved.mes_ref_final} (fonte: {resolved.override_source})")

            # 1) Colunas solicitadas (se vazio = padrão)
            if sys.stdin.isatty():
                columns_request = selected_columns_cli  # pode ser [], que significa "padrão"
            else:
                columns_request = resolved.visible_columns or selected_columns_cli or []

            # 1.1) Preferência vinda do portal (por unidade)
            nu_key = normalize_unit(unidade)
            povr = portal_overrides_norm.get(nu_key) if nu_key else None
            if isinstance(povr, dict):
                portal_cols = povr.get("visible_columns") or povr.get("columns")
                if isinstance(portal_cols, list) and portal_cols:
                    columns_request = portal_cols

            # 1.1) Preferência do portal por unidade (Configurações -> colunas)
            try:
                nu = normalize_unit(unidade)
                portal_unit_cfg = portal_overrides_norm.get(nu) if nu else None
                cols_portal = portal_unit_cfg.get("columns") if isinstance(portal_unit_cfg, dict) else None
                if isinstance(cols_portal, list) and cols_portal:
                    columns_request = cols_portal
            except Exception:
                pass

            # 2) Processamento (filtra + monta rows e colunas)
            rows, recipients, summary = filter_and_prepare(
                df,
                unidade,
                resolved.mes_ref_final,
                columns_whitelist=columns_request or None,
            )

            # 2.1) Mês anterior (para KPIs com comparação)
            def _prev_month(ym: str) -> str:
                try:
                    y = int(ym[:4]); m = int(ym[-2:])
                    if m == 1:
                        return f"{y-1:04d}-12"
                    return f"{y:04d}-{m-1:02d}"
                except Exception:
                    # fallback: usa utils.previous_month_from_today (não ideal, mas evita quebra)
                    from utils import previous_month_from_today
                    return previous_month_from_today()

            prev_ym = _prev_month(resolved.mes_ref_final)
            try:
                rows_prev, _rec_prev, sum_prev = filter_and_prepare(
                    df,
                    unidade,
                    prev_ym,
                    columns_whitelist=columns_request or None,
                )
            except Exception:
                rows_prev = []
                sum_prev = None

            # 2.2) YTD: lista de linhas por mês (desde janeiro até o mês atual)
            def _ytd_months(ym: str) -> list[str]:
                y = int(ym[:4]); m = int(ym[-2:])
                return [f"{y:04d}-{mm:02d}" for mm in range(1, m + 1)]

            rows_ytd: list[list[dict]] = []
            rows_ytd_prev: list[list[dict]] = []
            try:
                for ym_it in _ytd_months(resolved.mes_ref_final):
                    r_it, _r0, _s0 = filter_and_prepare(
                        df,
                        unidade,
                        ym_it,
                        columns_whitelist=columns_request or None,
                    )
                    rows_ytd.append(r_it)
                # YTD até o mês anterior (para tendência YTD opcional)
                prev_list = _ytd_months(prev_ym)
                for ym_it in prev_list:
                    r_it, _r0, _s0 = filter_and_prepare(
                        df,
                        unidade,
                        ym_it,
                        columns_whitelist=columns_request or None,
                    )
                    rows_ytd_prev.append(r_it)
            except Exception:
                rows_ytd = []
                rows_ytd_prev = []

            if not rows:
                print(f"[WARN] Sem dados para unidade '{unidade}' no mes {resolved.mes_ref_final}; pulando.")
                continue

            missing_columns = summary.get("missing_columns") if isinstance(summary, dict) else []
            if missing_columns:
                for col in missing_columns:
                    print(f"[WARN] Coluna solicitada '{col}' nao encontrada; ignorando.")
            if summary.get("fallback_used"):
                print("[WARN] Nenhuma coluna configurada disponivel; usando colunas de seguranca.")

            if not recipients and fallback_email:
                recipients = [fallback_email]

            destinatarios_display = "; ".join(recipients)

            # 3) *** Colunas do HTML ***
            #    SEMPRE usamos a ordem calculada pelo processor (display_columns),
            #    pois ela já inclui/posiciona as extras e evita descompasso com 'rows'.
            table_columns_for_html = summary.get("display_columns") or list(DEFAULT_DISPLAY_COLUMNS)

            # 4) Textos (copy)
            upper_to_lower = {
                "COPY_GREETING": "greeting",
                "COPY_INTRO": "intro",
                "COPY_OBSERVATION": "observation",
                "COPY_OBS": "observation",
                "COPY_REMINDER": "reminder",
                "COPY_CTA_LABEL": "cta_label",
                "COPY_FOOTER_SIGNATURE": "footer_signature",
            }
            copy_from_overrides: Dict[str, str] = {}
            for key, value in (resolved.copy or {}).items():
                mapped = upper_to_lower.get(key)
                if mapped:
                    copy_from_overrides[mapped] = value
            final_copy: Dict[str, str] = {**copy_from_overrides, **copy_overrides_cli}

            # 4.1) Integração: textos salvos no portal para a unidade
            nu = normalize_unit(unidade)
            portal_unit = portal_overrides_norm.get(nu) if nu else None
            if isinstance(portal_unit, dict):
                # sobrescrever qualquer copy explicitamente definida (até mesmo vazia)
                for k in ["greeting","intro","observation","reminder","cta_label","footer_signature"]:
                    if k in portal_unit:
                        final_copy[k] = str(portal_unit.get(k) or "")
                # SUBJECT_TEMPLATE
                subj = portal_unit.get("SUBJECT_TEMPLATE")
                if isinstance(subj, str):
                    subject_template = subj
                # texto adicional -> acrescenta ao fim da observação
                extra_txt = str(portal_unit.get("texto", "")).strip()
                if extra_txt:
                    base_obs = final_copy.get("observation") or ""
                    if base_obs:
                        final_copy["observation"] = base_obs + "<br>" + extra_txt
                    else:
                        final_copy["observation"] = extra_txt

            # 5) Render
            html = emailer.render_html(
                unidade=unidade,
                regiao=args.regiao,
                ym=resolved.mes_ref_final,
                rows=rows,
                rows_prev=rows_prev,
                rows_ytd=rows_ytd,
                rows_ytd_prev=rows_ytd_prev,
                summary=summary,
                destinatarios_exibicao=destinatarios_display,
                copy_overrides=final_copy,
                table_columns=table_columns_for_html,
                # extras para debug de totais prévios no template
                extra_prev=sum_prev or {},
            )

            # --- DEBUG: imprime decisão de colunas e amostra do retroativo ---
            if args.dry_run:
                requested_cols = summary.get("requested_columns") or columns_request or []
                processed_cols = summary.get("display_columns") or []
                sample_retro = summary.get("sample_desconto_sla_retroativo", [])
                rescue_src = summary.get("rescue_source_desconto_sla_retroativo", "")
                debug_like = summary.get("debug_columns_like_retro", [])
                retro_before = summary.get("retro_debug_before", [])
                retro_after = summary.get("retro_debug_after", [])
                _debug_print_columns(requested_cols, processed_cols, table_columns_for_html)
                print(f"[DEBUG] 'Desconto SLA Retroativo' (amostra 5): {sample_retro}")
                if rescue_src:
                    print(f"[DEBUG] Rescue source (copiado de): '{rescue_src}'")
                if debug_like:
                    print(f"[DEBUG] Colunas com 'retro' no nome: {debug_like}")
                if retro_before:
                    print(f"[DEBUG] Retroativo BEFORE normalize (head): {retro_before}")
                if retro_after:
                    print(f"[DEBUG] Retroativo AFTER normalize (head):  {retro_after}")
                print()

            output_dir.mkdir(parents=True, exist_ok=True)
            html_path = save_html(output_dir, unidade, resolved.mes_ref_final, html)
            if args.preview:
                try:
                    webbrowser.open(f"file://{html_path}")
                except Exception:
                    pass

            subject_template = resolved.subject_template or resolved.copy.get("SUBJECT_TEMPLATE") if resolved else None
            subject_template = copy_overrides_cli.get("SUBJECT_TEMPLATE", subject_template)
            subject = emailer.subject(
                unidade,
                resolved.mes_ref_final,
                regiao=args.regiao,
                template=subject_template,
                copy_overrides=final_copy,
            )

            if not recipients:
                raise RuntimeError("Nenhum destinatario encontrado e FALLBACK_EMAIL nao configurado.")

            status = "saved"
            error_txt = ""

            if not args.dry_run:
                if (not args.allow_resend) and has_successful_send(db_path, args.regiao, unidade, resolved.mes_ref_final):
                    raise RuntimeError(f"Ja existe envio registrado para {unidade} em {resolved.mes_ref_final}.")
                
                sender_email = env_cfg.get("SENDER_EMAIL", "")
                sender_name = env_cfg.get("SENDER_NAME", "")
                
                # Decide entre SendGrid ou Outlook
                use_sendgrid = env_cfg.get("USE_SENDGRID", "false").lower() == "true"
                
                if use_sendgrid:
                    # Envia via SendGrid
                    sendgrid_from = env_cfg.get("SENDGRID_FROM_EMAIL", sender_email)
                    sendgrid_name = env_cfg.get("SENDGRID_FROM_NAME", sender_name)
                    emailer.send_sendgrid(
                        subject=subject,
                        html=html,
                        recipients=recipients,
                        sender_email=sendgrid_from,
                        sender_name=sendgrid_name,
                        attachments=[]
                    )
                    print(f"[INFO] E-mail enviado via SendGrid para {unidade}")
                else:
                    # Envia via Outlook (método original)
                    emailer.send_outlook(
                        subject=subject,
                        html=html,
                        recipients=recipients,
                        sender_email=sender_email,
                        attachments=[]
                    )
                    print(f"[INFO] E-mail enviado via Outlook para {unidade}")
                
                status = "resent" if args.allow_resend else "sent"

            log_sqlite(
                db_path,
                {
                    "ts": date.today().isoformat(),
                    "regiao": args.regiao,
                    "unidade": unidade,
                    "mes": resolved.mes_ref_final,
                    "dry_run": 1 if args.dry_run else 0,
                    "status": status,
                    "subject": subject,
                    "recipients": destinatarios_display,
                    "html_path": str(html_path),
                    "workbook_path": str(workbook),
                    "sheet_name": sheet_name,
                    "row_count": summary.get("row_count", 0) if summary else 0,
                    "sum_valor_mensal_final": summary.get("sum_valor_mensal_final", 0.0) if summary else 0.0,
                    "override_source": resolved.override_source,
                    "visible_columns": ",".join(table_columns_for_html or []),
                    "error": error_txt,
                },
            )

            total_processed += 1

        except (OverrideConfigError, RuntimeError) as exc:
            errors += 1
            print(f"[ERROR] Falha na unidade '{unidade}': {exc}")
            mes_log = resolved.mes_ref_final if resolved else (cli_mes or resolve_auto_month(env_cfg, unidade))
            table_columns_for_html = summary.get("display_columns") if summary else []
            log_sqlite(
                db_path,
                {
                    "ts": date.today().isoformat(),
                    "regiao": args.regiao,
                    "unidade": unidade,
                    "mes": mes_log,
                    "dry_run": 1 if args.dry_run else 0,
                    "status": "failed",
                    "subject": "",
                    "recipients": "",
                    "html_path": "",
                    "workbook_path": str(workbook),
                    "sheet_name": sheet_name,
                    "row_count": summary.get("row_count", 0) if summary else 0,
                    "sum_valor_mensal_final": summary.get("sum_valor_mensal_final", 0.0) if summary else 0.0,
                    "override_source": resolved.override_source if resolved else "",
                    "visible_columns": ",".join(table_columns_for_html or []),
                    "error": str(exc),
                },
            )
        except Exception as exc:
            errors += 1
            print(f"[ERROR] Erro inesperado na unidade '{unidade}': {exc}")
            mes_log = resolved.mes_ref_final if resolved else (cli_mes or resolve_auto_month(env_cfg, unidade))
            table_columns_for_html = summary.get("display_columns") if summary else []
            log_sqlite(
                db_path,
                {
                    "ts": date.today().isoformat(),
                    "regiao": args.regiao,
                    "unidade": unidade,
                    "mes": mes_log,
                    "dry_run": 1 if args.dry_run else 0,
                    "status": "failed",
                    "subject": "",
                    "recipients": "",
                    "html_path": "",
                    "workbook_path": str(workbook),
                    "sheet_name": sheet_name,
                    "row_count": summary.get("row_count", 0) if summary else 0,
                    "sum_valor_mensal_final": summary.get("sum_valor_mensal_final", 0.0) if summary else 0.0,
                    "override_source": resolved.override_source if resolved else "",
                    "visible_columns": ",".join(table_columns_for_html or []),
                    "error": str(exc),
                },
            )

    print(f"[INFO] Finalizado. Unidades processadas: {total_processed}. Erros: {errors}. Saida: {output_dir}")

if __name__ == "__main__":
    main()
