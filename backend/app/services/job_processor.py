# job_processor.py — Serviço de processamento de jobs

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import dotenv_values

from app.models.job import ProcessingJob
# Importa módulos core da raiz (elimina duplicação)
from app.services.core_imports import Extractor, filter_and_prepare, map_columns, Emailer

# Configuração de logging
logger = logging.getLogger(__name__)

# Diretórios base (relativos à raiz do projeto)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # backpperformance/
BACKEND_DIR = BASE_DIR / "backend"
UPLOAD_DIR = BACKEND_DIR / "uploads"
OUTPUT_DIR = BACKEND_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"

# Garante que diretórios existem
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class JobProcessorError(Exception):
    """Erro durante processamento de job."""
    pass


class JobProcessor:
    """
    Serviço responsável pelo processamento de jobs de planilhas.
    
    Fluxo:
    1. Carrega arquivo Excel do job
    2. Extrai dados da aba correta
    3. Processa dados com filter_and_prepare
    4. Gera HTML do relatório
    5. Salva resultado e atualiza status do job
    """
    
    def __init__(self, db: Session):
        self.db = db
        self._env_config_cache: Optional[Dict[str, str]] = None
    
    def _load_env_config(self) -> Dict[str, str]:
        """Carrega configurações do .env para o Emailer."""
        if self._env_config_cache is not None:
            return self._env_config_cache
        
        # Tenta carregar de múltiplos arquivos .env
        env_files = [
            BASE_DIR / ".env",
            BACKEND_DIR / ".env",
        ]
        
        config: Dict[str, str] = {}
        for env_file in env_files:
            if env_file.exists():
                loaded = dotenv_values(str(env_file))
                config.update({k: str(v) for k, v in loaded.items() if v is not None})
        
        # Também pega do ambiente do sistema
        for key in os.environ:
            if key.startswith("COPY_") or key.startswith("LOGO_") or key.startswith("BRAND_"):
                config[key] = os.environ[key]
        
        # Valores padrão essenciais
        config.setdefault("SENDER_NAME", "Equipe Financeira")
        config.setdefault("SENDER_EMAIL", "financeiro@empresa.com")
        
        self._env_config_cache = config
        return config
    
    def get_job(self, job_id: int) -> Optional[ProcessingJob]:
        """Busca job pelo ID."""
        return self.db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    
    def update_job_status(
        self, 
        job: ProcessingJob, 
        status: str, 
        error_message: Optional[str] = None,
        result_summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """Atualiza status do job no banco."""
        job.status = status
        if error_message:
            job.error_message = error_message
        if result_summary:
            job.result_summary = result_summary
        job.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(job)
    
    def extract_metadata_from_file(self, file_path: Path, region: str) -> Dict[str, Any]:
        """
        Extrai metadados do arquivo Excel (unidades disponíveis, meses, etc).
        
        Args:
            file_path: Caminho do arquivo Excel
            region: Código da região (SP1, RJ, NNE, etc)
        
        Returns:
            Dicionário com metadados extraídos
        """
        extractor = Extractor(file_path.parent)
        
        try:
            df, sheet_name = extractor.read_region_sheet(file_path, region)
        except RuntimeError as e:
            raise JobProcessorError(f"Erro ao ler planilha: {str(e)}")
        
        # Mapeia colunas
        col_mapping = map_columns(df, warn_missing=False)
        
        # Extrai unidades únicas
        uni_col = col_mapping.get("Unidade")
        units = []
        if uni_col and uni_col in df.columns:
            units = df[uni_col].dropna().astype(str).str.strip().unique().tolist()
            units = [u for u in units if u and u.lower() not in ('', 'nan', 'none')]
        
        # Extrai meses disponíveis
        mes_col = col_mapping.get("Mes_Emissao_NF") or col_mapping.get("Mês_Emissão_NF")
        months = []
        if mes_col and mes_col in df.columns:
            from app.services.utils import normalize_text_full
            from app.services.processor import _vectorized_parse_year_month
            
            parsed = _vectorized_parse_year_month(df[mes_col])
            months = parsed.dropna().unique().tolist()
            months = [m for m in months if m]
            months.sort(reverse=True)  # Mais recente primeiro
        
        return {
            "sheet_name": sheet_name,
            "units": sorted(units),
            "months": months,
            "row_count": len(df),
            "columns": list(df.columns),
            "column_mapping": {k: v for k, v in col_mapping.items() if v}
        }
    
    def process_job(
        self,
        job_id: int,
        region: str,
        unit: str,
        month: str,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Processa um job completo.
        
        Args:
            job_id: ID do job no banco
            region: Código da região (SP1, RJ, etc)
            unit: Nome da unidade a processar
            month: Mês de referência (YYYY-MM)
            dry_run: Se True, não envia emails
        
        Returns:
            Dicionário com resultado do processamento
        
        Raises:
            JobProcessorError: Em caso de erro no processamento
        """
        # 1. Busca job
        job = self.get_job(job_id)
        if not job:
            raise JobProcessorError(f"Job {job_id} não encontrado")
        
        if job.status == "processing":
            raise JobProcessorError(f"Job {job_id} já está em processamento")
        
        if job.status == "completed":
            # Permite reprocessar, mas loga
            logger.info(f"Reprocessando job {job_id} já completado")
        
        # 2. Atualiza status para processing
        self.update_job_status(job, "processing")
        
        try:
            # 3. Valida arquivo
            file_path = Path(job.file_url)
            if not file_path.exists():
                raise JobProcessorError(f"Arquivo não encontrado: {file_path}")
            
            # 4. Extrai dados da planilha
            extractor = Extractor(file_path.parent)
            df, sheet_name = extractor.read_region_sheet(file_path, region)
            
            logger.info(f"Job {job_id}: Planilha carregada ({len(df)} linhas, aba: {sheet_name})")
            
            # 5. Processa dados
            rows, recipients, summary = filter_and_prepare(
                df=df,
                unidade=unit,
                ym=month,
                columns_whitelist=None  # Usa colunas padrão
            )
            
            if not rows:
                raise JobProcessorError(
                    f"Nenhum dado encontrado para unidade '{unit}' no mês '{month}'"
                )
            
            logger.info(f"Job {job_id}: {len(rows)} linhas processadas para {unit}")
            
            # 6. Gera HTML do relatório usando Emailer
            env_cfg = self._load_env_config()
            emailer = Emailer(
                templates_dir=TEMPLATES_DIR,
                assets_dir=ASSETS_DIR,
                env_cfg=env_cfg
            )
            
            # Formata destinatários para exibição
            destinatarios_exibicao = "; ".join(recipients) if recipients else ""
            
            html_content = emailer.render_html(
                unidade=unit,
                regiao=region,
                ym=month,
                rows=rows,
                summary=summary,
                destinatarios_exibicao=destinatarios_exibicao,
            )
            
            # 7. Salva HTML no disco
            safe_unit = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in unit)
            output_filename = f"{safe_unit}_{month}.html"
            output_path = OUTPUT_DIR / output_filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Job {job_id}: HTML salvo em {output_path}")
            
            # 8. Monta resultado
            result = {
                "row_count": summary["row_count"],
                "sum_valor_mensal_final": summary["sum_valor_mensal_final"],
                "recipients": recipients,
                "output_file": str(output_path),
                "output_filename": output_filename,
                "dry_run": dry_run,
                "unit": unit,
                "month": month,
                "region": region,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # 9. Atualiza job com sucesso
            job.region = region
            job.month_ref = month
            self.update_job_status(
                job, 
                "completed",
                result_summary=result
            )
            
            return result
            
        except JobProcessorError as e:
            # Re-raise erros conhecidos após atualizar status
            self.update_job_status(job, "failed", error_message=str(e))
            raise
        except Exception as e:
            # Captura erros inesperados
            error_msg = f"Erro inesperado: {type(e).__name__}: {str(e)}"
            logger.exception(f"Job {job_id}: {error_msg}")
            self.update_job_status(job, "failed", error_message=error_msg)
            raise JobProcessorError(error_msg) from e
    
    def get_job_result_file(self, job_id: int) -> Optional[Tuple[Path, str]]:
        """
        Retorna caminho do arquivo de resultado de um job.
        
        Returns:
            Tupla (path, filename) ou None se não existir
        """
        job = self.get_job(job_id)
        if not job or not job.result_summary:
            return None
        
        output_file = job.result_summary.get("output_file")
        if not output_file:
            return None
        
        path = Path(output_file)
        if not path.exists():
            return None
        
        filename = job.result_summary.get("output_filename", path.name)
        return (path, filename)
