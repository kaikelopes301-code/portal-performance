from pathlib import Path
import pandas as pd
import re
from extractor import Extractor

from processor import _norm as p_norm, map_columns  # type: ignore
from utils import parse_year_month, normalize_unit

# Config
xlsx_path = Path(r"C:\backpperformance\planilhas\Planilha de Controle Contratos - Medição Mensal_SP1_2025.xlsx")
regiao = "SP1"
ym = "2025-08"

ext = Extractor(xlsx_path.parent)

# Use same logic as app
df, sheet = ext.read_region_sheet(xlsx_path, regiao)
print(f"[INFO] Sheet selecionada: {sheet}")
print(f"[INFO] Qtd colunas: {len(df.columns)}")

# List columns with tokens
norm_cols = {c: p_norm(c) for c in df.columns}
print("\n[Cols contendo 'sla' e 'retro']")
for c, n in norm_cols.items():
    if ("sla" in n) and ("retro" in n or "retr" in n):
        print(" -", c)

print("\n[Amostra valores brutos - primeiras 10 linhas]")
cols_interest = []
for c in df.columns:
    n = norm_cols[c]
    if ("sla" in n and ("retro" in n or "retr" in n)) or ("dissidio" in n or "dissidio" in n.replace("í","i")):
        cols_interest.append(c)

print("Colunas de interesse:", cols_interest)
print()

if cols_interest:
    print(df[cols_interest].head(10).to_string(index=False))
else:
    print("Nenhuma coluna de interesse encontrada.")

# === Filtrar por mês/unidade como no processor ===
mapping = map_columns(df)
uni_col = mapping.get("Unidade")
mes_col = mapping.get("Mes_Emissão_NF") or mapping.get("Mes_Emissao_NF")
print(f"\n[Mapping] unidade='{uni_col}' mes='{mes_col}'")

if uni_col and mes_col:
    ym_series = df[mes_col].apply(parse_year_month)
    dfm = df.loc[ym_series == ym].copy()
    print(f"[INFO] Linhas para {ym}: {len(dfm)}")
    units = sorted(dfm[uni_col].dropna().astype(str).unique())
    print(f"[INFO] Unidades detectadas ({len(units)}): {units}")

    target_cols = [c for c in df.columns if p_norm(c) == p_norm('Desconto SLA Retroativo')]
    if not target_cols:
        # tentar por tokens
        for c in df.columns:
            n = p_norm(c)
            if ('sla' in n) and ('retro' in n or 'retr' in n):
                target_cols.append(c)
    print(f"[INFO] Coluna alvo retroativo detectada: {target_cols}")

    for u in units:
        nu = normalize_unit(u)
        sub = dfm.loc[dfm[uni_col].astype(str).map(normalize_unit) == nu]
        if not sub.empty:
            print(f"\n--- {u} ---")
            if target_cols:
                col = target_cols[0]
                vals = sub[col].head(10).astype(str).tolist()
                print(f"Retroativo (primeiras 10): {vals}")
            else:
                print("Retroativo: coluna não encontrada dentro do mês recortado.")
else:
    print("[WARN] Não foi possível determinar colunas de unidade/mês.")
