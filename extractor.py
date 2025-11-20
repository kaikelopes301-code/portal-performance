from pathlib import Path
import pandas as pd
import re
from typing import Optional, Tuple

class Extractor:
    def __init__(self, xlsx_dir: Path):
        self.xlsx_dir = Path(xlsx_dir)

    def find_workbook(self, regiao: str) -> Optional[Path]:
        patterns = [
            f"*planilha *Medição Mensal*_{regiao}_*.xlsx",
            f"*Medição Mensal*_{regiao}.xlsx",
            f"*Medição*{regiao}*.xlsx",
        ]
        for pat in patterns:
            matches = sorted(self.xlsx_dir.glob(pat))
            # ignora arquivos temporários de lock do Excel (~$*.xlsx)
            matches = [m for m in matches if not m.name.startswith("~$")]
            if matches:
                matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                return matches[0]
        # Fallback: qualquer .xlsx com aba parecida
        for p in sorted(self.xlsx_dir.glob("*.xlsx")):
            if p.name.startswith("~$"):
                continue
            try:
                xl = pd.ExcelFile(p)
                target = f"Faturamento {regiao}".lower().strip()
                for s in xl.sheet_names:
                    if s.lower().strip() == target or target in s.lower().strip():
                        return p
            except Exception:
                continue
        return None

    def read_region_sheet(self, path: Path, regiao: str) -> Tuple[pd.DataFrame, str]:
        target = f"Faturamento {regiao}".lower().strip()
        xl = pd.ExcelFile(path)
        sheet_name = None
        for s in xl.sheet_names:
            if s.lower().strip() == target or target in s.lower().strip():
                sheet_name = s
                break
        if sheet_name is None:
            raise RuntimeError(
                f"Aba com nome semelhante a 'Faturamento {regiao}' não encontrada em {path.name}. Abas: {xl.sheet_names}"
            )

        
        df = pd.read_excel(path, sheet_name=sheet_name, dtype=object)

        def _clean_header(h) -> str:
            s = "" if h is None else str(h)
            # NBSP / &nbsp; / quebras
            s = s.replace("\u00A0", " ").replace("&nbsp;", " ")
            s = s.replace("\r", " ").replace("\n", " ")
            # colapsa espaços
            s = re.sub(r"\s+", " ", s)
            return s.strip()

        # limpa cabeçalhos agressivamente (remove quebras que causavam o bug)
        df.columns = [_clean_header(c) for c in df.columns]

        # strip de valores em todas as colunas (mantendo strings)
        for c in df.columns:
            try:
                df[c] = df[c].apply(
                    lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v))
                    else str(v).strip()
                )
            except Exception:
                pass

        return df, sheet_name
