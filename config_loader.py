from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils import normalize_unit, parse_year_month, previous_month_from_today, safe_read_text, safe_parse_json


_ENV_KEY = "UNIT_OVERRIDES_JSON"
_DEFAULT_RELATIVE_PATH = Path("config") / "overrides.json"
_OFFSET_PATTERN = re.compile(r"^offset:(?P<sign>[+-])(?P<value>\d+)M$", re.IGNORECASE)


class OverrideConfigError(ValueError):
    """Raised when an overrides configuration is invalid."""


@dataclass
class ResolvedConfig:
    visible_columns: List[str]
    copy: Dict[str, str]
    mes_ref_final: str
    override_source: str
    subject_template: Optional[str] = None
    requested_columns: List[str] = None

    def as_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "visible_columns": self.visible_columns,
            "copy": self.copy,
            "mes_ref_final": self.mes_ref_final,
            "override_source": self.override_source,
        }
        if self.subject_template is not None:
            data["subject_template"] = self.subject_template
        if self.requested_columns is not None:
            data["requested_columns"] = self.requested_columns
        return data


_OVERRIDES: Dict[str, Any] = {"defaults": {}, "regions": {}, "units": {}}


def load_overrides(
    overrides_path: Optional[str] = None,
    *,
    base_dir: Optional[Path] = None,
    env_json: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Load overrides configuration applying precedence:
      1) explicit path passed via CLI flag
      2) default config/overrides.json relative to project root
      3) UNIT_OVERRIDES_JSON environment value (usually from .env)
    """

    base_dir = base_dir or Path.cwd()

    raw_data: Dict[str, Any] = {}
    source_label = ""

    if overrides_path:
        path = Path(overrides_path)
        if not path.is_absolute():
            path = (base_dir / overrides_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Overrides file not found: {path}")
        raw_data = _parse_json(safe_read_text(path), source=str(path))
        source_label = str(path)
    else:
        candidate = (base_dir / _DEFAULT_RELATIVE_PATH).resolve()
        if candidate.exists():
            raw_data = _parse_json(safe_read_text(candidate), source=str(candidate))
            source_label = str(candidate)

    if not raw_data:
        env_payload = env_json if env_json is not None else os.environ.get(_ENV_KEY, "")
        if env_payload.strip():
            raw_data = _parse_json(env_payload, source=f"env:{_ENV_KEY}")
            source_label = f"env:{_ENV_KEY}"

    normalized = _normalize_overrides(raw_data)
    _OVERRIDES.clear()
    _OVERRIDES.update(normalized)
    _OVERRIDES["__source__"] = source_label
    return dict(_OVERRIDES)


def resolve_overrides(
    regiao: str,
    unidade: str,
    cli_mes: Optional[str],
    force_mes: Optional[str],
    *,
    auto_mes: Optional[str] = None,
    today: Optional[date] = None,
) -> ResolvedConfig:
    """Compute the effective overrides for the given unit and region."""

    today = today or date.today()
    normalized_unit = normalize_unit(unidade)
    reg_key = (regiao or "").strip().upper()

    data = _OVERRIDES or {"defaults": {}, "regions": {}, "units": {}}
    defaults = data.get("defaults", {}) or {}
    regions = data.get("regions", {}) or {}
    units = data.get("units", {}) or {}

    unit_cfg = units.get(normalized_unit, {})
    region_cfg = regions.get(reg_key, {})

    defaults_columns = list(defaults.get("visible_columns", []) or [])
    region_columns = list(region_cfg.get("visible_columns", []) or [])
    unit_columns = list(unit_cfg.get("visible_columns", []) or [])

    requested_columns = unit_columns or region_columns or defaults_columns
    visible_columns = list(requested_columns)

    merged_copy: Dict[str, str] = {}
    for scope in (defaults, region_cfg, unit_cfg):
        scope_copy = scope.get("copy", {}) if isinstance(scope, dict) else {}
        for key, value in scope_copy.items():
            if value is None:
                continue
            merged_copy[str(key)] = str(value)

    subject_template = merged_copy.get("SUBJECT_TEMPLATE")

    force_month = _ensure_optional_year_month(force_mes, flag_name="--force-mes")
    cli_month = _ensure_optional_year_month(cli_mes, flag_name="--mes")
    auto_month = _ensure_optional_year_month(auto_mes, flag_name="auto") or previous_month_from_today(today)

    month_choices: List[Tuple[str, Optional[str]]] = [
        ("unit", unit_cfg.get("month_reference")),
        ("region", region_cfg.get("month_reference")),
        ("default", defaults.get("month_reference")),
    ]

    mes_ref_final: Optional[str] = None
    override_source = ""

    if force_month:
        mes_ref_final = force_month
        override_source = "force"
    else:
        chosen_scope = None
        for scope_name, raw in month_choices:
            if raw is not None:
                mes_ref_final = _materialize_month(raw, today=today, auto_month=auto_month, scope_name=scope_name)
                chosen_scope = scope_name
                break
        if mes_ref_final:
            override_source = chosen_scope or "default"
        elif cli_month:
            mes_ref_final = cli_month
            override_source = "cli"
        else:
            mes_ref_final = auto_month
            override_source = "default"

    if not mes_ref_final:
        raise OverrideConfigError("Unable to resolve month reference for processing.")

    return ResolvedConfig(
        visible_columns=visible_columns,
        copy=merged_copy,
        mes_ref_final=mes_ref_final,
        override_source=override_source,
        subject_template=subject_template,
        requested_columns=visible_columns,
    )


def get_loaded_overrides() -> Dict[str, Any]:
    """Expose the currently loaded overrides (for debugging/testing)."""

    return dict(_OVERRIDES)


def _parse_json(payload: str, *, source: str) -> Dict[str, Any]:
    payload = (payload or '').strip()
    if not payload:
        return {}
    try:
        data = safe_parse_json(payload)
    except json.JSONDecodeError as exc:
        raise OverrideConfigError('Invalid JSON. Tip: save as UTF-8 (no BOM). Common causes: trailing commas, // comments.') from exc
    if not isinstance(data, dict):
        raise OverrideConfigError(f"Overrides root in {source} must be a JSON object.")
    return data


def _normalize_overrides(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not data:
        return {"defaults": {}, "regions": {}, "units": {}}

    if not isinstance(data, dict):
        raise OverrideConfigError("Overrides payload must be a JSON object.")

    defaults = _normalize_scope(data.get("defaults"), scope_name="defaults")
    regions_raw = data.get("regions", {})
    if regions_raw and not isinstance(regions_raw, dict):
        raise OverrideConfigError("'regions' must be an object with region codes as keys.")

    regions: Dict[str, Dict[str, Any]] = {}
    for key, value in (regions_raw or {}).items():
        if not isinstance(key, str) or not key.strip():
            raise OverrideConfigError("Region keys must be non-empty strings.")
        region_key = key.strip().upper()
        regions[region_key] = _normalize_scope(value, scope_name=f"regions['{key}']")

    units_raw = data.get("units", {})
    if units_raw and not isinstance(units_raw, dict):
        raise OverrideConfigError("'units' must be an object with unit names as keys.")

    units: Dict[str, Dict[str, Any]] = {}
    for key, value in (units_raw or {}).items():
        if not isinstance(key, str) or not key.strip():
            raise OverrideConfigError("Unit keys must be non-empty strings.")
        normalized_key = normalize_unit(key)
        if not normalized_key:
            raise OverrideConfigError(f"Unit key '{key}' normalizes to empty string.")
        if normalized_key in units:
            other = units[normalized_key].get("__label__", key)
            raise OverrideConfigError(
                f"Duplicate unit override after normalization: '{key}' conflicts with '{other}'."
            )
        units[normalized_key] = _normalize_scope(value, scope_name=f"units['{key}']")
        units[normalized_key]["__label__"] = key

    return {"defaults": defaults, "regions": regions, "units": units}


def _normalize_scope(section: Any, *, scope_name: str) -> Dict[str, Any]:
    if not section:
        return {}
    if not isinstance(section, dict):
        raise OverrideConfigError(f"{scope_name} must be a JSON object.")

    result: Dict[str, Any] = {}

    if "visible_columns" in section:
        cols = section["visible_columns"]
        if cols is None:
            result["visible_columns"] = []
        elif isinstance(cols, list):
            cleaned = [str(item).strip() for item in cols if str(item).strip()]
            result["visible_columns"] = cleaned
        else:
            raise OverrideConfigError(f"{scope_name}.visible_columns must be a list of strings.")

    if "copy" in section:
        copy_section = section["copy"]
        if copy_section is None:
            result["copy"] = {}
        elif isinstance(copy_section, dict):
            copy_clean: Dict[str, str] = {}
            for key, value in copy_section.items():
                if value is None:
                    continue
                copy_clean[str(key)] = str(value)
            result["copy"] = copy_clean
        else:
            raise OverrideConfigError(f"{scope_name}.copy must be an object.")

    if "month_reference" in section:
        result["month_reference"] = _normalize_month_mode(section["month_reference"], scope_name=scope_name)

    return result


def _normalize_month_mode(value: Any, *, scope_name: str) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise OverrideConfigError(f"{scope_name}.month_reference must be a string.")
    raw = value.strip()
    if not raw:
        return None

    lowered = raw.lower()
    if lowered == "auto":
        return "auto"

    normalized = parse_year_month(raw)
    if normalized:
        return normalized

    match = _OFFSET_PATTERN.match(lowered)
    if match:
        sign = -1 if match.group("sign") == "-" else 1
        step = int(match.group("value"))
        return f"offset:{'+' if sign >= 0 else '-'}{step}M"

    raise OverrideConfigError(
        f"{scope_name}.month_reference must be 'auto', 'YYYY-MM' or 'offset:+nM/-nM'. Got: {value!r}."
    )


def _materialize_month(
    raw: Any,
    *,
    today: date,
    auto_month: str,
    scope_name: str,
) -> str:
    if raw is None:
        raise OverrideConfigError(f"{scope_name} month reference is missing.")
    if not isinstance(raw, str):
        raise OverrideConfigError(f"{scope_name} month reference must be a string.")

    lowered = raw.lower().strip()
    if lowered == "auto":
        return auto_month

    normalized = parse_year_month(raw)
    if normalized:
        return normalized

    match = _OFFSET_PATTERN.match(lowered)
    if match:
        sign = -1 if match.group("sign") == "-" else 1
        step = int(match.group("value"))
        delta = sign * step
        return _shift_month(today, delta)

    raise OverrideConfigError(
        f"Invalid month reference '{raw}' for scope {scope_name}. Expected 'auto', 'YYYY-MM' or 'offset:+nM/-nM'."
    )


def _shift_month(anchor: date, delta: int) -> str:
    year = anchor.year
    month = anchor.month
    total = year * 12 + (month - 1) + delta
    new_year = total // 12
    new_month = total % 12 + 1
    return f"{new_year:04d}-{new_month:02d}"


def _ensure_optional_year_month(value: Optional[str], *, flag_name: str) -> Optional[str]:
    if value is None:
        return None
    parsed = parse_year_month(value)
    if not parsed:
        raise OverrideConfigError(f"{flag_name} must be provided in 'YYYY-MM' format. Received: {value!r}.")
    return parsed


