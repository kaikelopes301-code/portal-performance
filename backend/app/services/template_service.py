# template_service.py — Serviço de gerenciamento de templates

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import shutil
import re

logger = logging.getLogger(__name__)

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # backpperformance/
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_META_FILE = TEMPLATES_DIR / "templates_meta.json"

# Garante que diretório existe
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


class TemplateServiceError(Exception):
    """Erro no serviço de templates."""
    pass


class TemplateService:
    """
    Serviço para gerenciamento de templates de email.
    
    Templates são arquivos HTML armazenados no diretório templates/
    com metadados salvos em templates_meta.json
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self._meta_cache: Optional[Dict[str, Any]] = None
    
    def _load_meta(self) -> Dict[str, Any]:
        """Carrega metadados dos templates."""
        if not TEMPLATES_META_FILE.exists():
            # Cria arquivo de metadados inicial
            default_meta = {
                "templates": {
                    "email_template_dark": {
                        "name": "Template Padrão (Dark)",
                        "description": "Template premium com tema escuro para relatórios de medição",
                        "filename": "email_template_dark.html",
                        "subject_template": "Medição {unidade} - {mes_ref}",
                        "is_active": True,
                        "created_at": "2025-01-01T00:00:00",
                        "updated_at": None
                    }
                },
                "default_template": "email_template_dark"
            }
            self._save_meta(default_meta)
            return default_meta
        
        try:
            with open(TEMPLATES_META_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar metadados de templates: {e}")
            raise TemplateServiceError(f"Erro ao carregar metadados: {e}")
    
    def _save_meta(self, meta: Dict[str, Any]) -> None:
        """Salva metadados dos templates."""
        try:
            with open(TEMPLATES_META_FILE, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            self._meta_cache = None
        except Exception as e:
            logger.error(f"Erro ao salvar metadados: {e}")
            raise TemplateServiceError(f"Erro ao salvar metadados: {e}")
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Lista todos os templates disponíveis."""
        meta = self._load_meta()
        templates = []
        
        for template_id, template_meta in meta.get("templates", {}).items():
            template_info = {
                "id": template_id,
                **template_meta
            }
            # Verifica se arquivo existe
            template_file = self.templates_dir / template_meta.get("filename", f"{template_id}.html")
            template_info["file_exists"] = template_file.exists()
            templates.append(template_info)
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Retorna metadados de um template específico."""
        meta = self._load_meta()
        template_meta = meta.get("templates", {}).get(template_id)
        
        if not template_meta:
            return None
        
        return {
            "id": template_id,
            **template_meta
        }
    
    def get_template_content(self, template_id: str) -> Optional[str]:
        """Retorna conteúdo HTML de um template."""
        template = self.get_template(template_id)
        if not template:
            return None
        
        filename = template.get("filename", f"{template_id}.html")
        template_path = self.templates_dir / filename
        
        if not template_path.exists():
            logger.error(f"Arquivo de template não encontrado: {template_path}")
            return None
        
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erro ao ler template: {e}")
            return None
    
    def create_template(
        self,
        template_id: str,
        name: str,
        content: str,
        description: Optional[str] = None,
        subject_template: str = "Medição {unidade} - {mes_ref}"
    ) -> Dict[str, Any]:
        """Cria um novo template."""
        meta = self._load_meta()
        
        # Valida ID
        if not re.match(r'^[a-zA-Z0-9_-]+$', template_id):
            raise TemplateServiceError("ID do template deve conter apenas letras, números, _ e -")
        
        if template_id in meta.get("templates", {}):
            raise TemplateServiceError(f"Template '{template_id}' já existe")
        
        # Salva arquivo HTML
        filename = f"{template_id}.html"
        template_path = self.templates_dir / filename
        
        try:
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise TemplateServiceError(f"Erro ao salvar arquivo de template: {e}")
        
        # Salva metadados
        template_meta = {
            "name": name,
            "description": description,
            "filename": filename,
            "subject_template": subject_template,
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None
        }
        
        if "templates" not in meta:
            meta["templates"] = {}
        
        meta["templates"][template_id] = template_meta
        self._save_meta(meta)
        
        return {
            "id": template_id,
            **template_meta
        }
    
    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        description: Optional[str] = None,
        subject_template: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Atualiza um template existente."""
        meta = self._load_meta()
        
        if template_id not in meta.get("templates", {}):
            raise TemplateServiceError(f"Template '{template_id}' não encontrado")
        
        template_meta = meta["templates"][template_id]
        
        # Atualiza conteúdo se fornecido
        if content is not None:
            filename = template_meta.get("filename", f"{template_id}.html")
            template_path = self.templates_dir / filename
            
            # Backup do arquivo anterior
            if template_path.exists():
                backup_path = self.templates_dir / f"{template_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                shutil.copy2(template_path, backup_path)
            
            try:
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                raise TemplateServiceError(f"Erro ao salvar arquivo de template: {e}")
        
        # Atualiza metadados
        if name is not None:
            template_meta["name"] = name
        if description is not None:
            template_meta["description"] = description
        if subject_template is not None:
            template_meta["subject_template"] = subject_template
        if is_active is not None:
            template_meta["is_active"] = is_active
        
        template_meta["updated_at"] = datetime.utcnow().isoformat()
        
        self._save_meta(meta)
        
        return {
            "id": template_id,
            **template_meta
        }
    
    def delete_template(self, template_id: str) -> bool:
        """Remove um template."""
        meta = self._load_meta()
        
        if template_id not in meta.get("templates", {}):
            return False
        
        # Não permite deletar template padrão
        if meta.get("default_template") == template_id:
            raise TemplateServiceError("Não é possível deletar o template padrão")
        
        template_meta = meta["templates"][template_id]
        filename = template_meta.get("filename", f"{template_id}.html")
        template_path = self.templates_dir / filename
        
        # Move arquivo para backup em vez de deletar
        if template_path.exists():
            backup_path = self.templates_dir / f"_deleted_{template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            shutil.move(template_path, backup_path)
        
        del meta["templates"][template_id]
        self._save_meta(meta)
        
        return True
    
    def get_default_template(self) -> str:
        """Retorna ID do template padrão."""
        meta = self._load_meta()
        return meta.get("default_template", "email_template_dark")
    
    def set_default_template(self, template_id: str) -> None:
        """Define template padrão."""
        meta = self._load_meta()
        
        if template_id not in meta.get("templates", {}):
            raise TemplateServiceError(f"Template '{template_id}' não encontrado")
        
        meta["default_template"] = template_id
        self._save_meta(meta)
    
    def preview_template(
        self,
        template_id: str,
        unit_name: str = "Shopping Exemplo",
        month_ref: str = "2025-11",
        sample_rows: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Gera preview de um template com dados de exemplo.
        """
        content = self.get_template_content(template_id)
        if not content:
            raise TemplateServiceError(f"Template '{template_id}' não encontrado ou sem conteúdo")
        
        # Dados de exemplo padrão
        if sample_rows is None:
            sample_rows = [
                {
                    "Unidade": unit_name,
                    "Categoria": "Limpeza",
                    "Fornecedor": "Fornecedor Exemplo",
                    "HC Planilha": "10",
                    "Dias Faltas": "2",
                    "Horas Atrasos": "1,5",
                    "Valor Planilha": "R$ 15.000,00",
                    "Desc. Falta Validado Atlas": "R$ 500,00",
                    "Desc. Atraso Validado Atlas": "R$ 150,00",
                    "Desconto SLA Mês": "R$ 0,00",
                    "Valor Mensal Final": "R$ 14.350,00",
                    "Mês de emissão da NF": "12/25"
                },
                {
                    "Unidade": unit_name,
                    "Categoria": "Segurança",
                    "Fornecedor": "Outro Fornecedor",
                    "HC Planilha": "5",
                    "Dias Faltas": "0",
                    "Horas Atrasos": "0",
                    "Valor Planilha": "R$ 8.000,00",
                    "Desc. Falta Validado Atlas": "R$ 0,00",
                    "Desc. Atraso Validado Atlas": "R$ 0,00",
                    "Desconto SLA Mês": "R$ 0,00",
                    "Valor Mensal Final": "R$ 8.000,00",
                    "Mês de emissão da NF": "12/25"
                }
            ]
        
        # Usa o Emailer para renderizar
        from app.services.emailer import Emailer
        from pathlib import Path
        import os
        
        # Carrega configurações do .env
        from dotenv import dotenv_values
        env_cfg = dict(dotenv_values(BASE_DIR / ".env"))
        env_cfg.setdefault("SENDER_NAME", "Equipe Financeira")
        env_cfg.setdefault("SENDER_EMAIL", "financeiro@empresa.com")
        
        emailer = Emailer(
            templates_dir=self.templates_dir,
            assets_dir=BASE_DIR / "assets",
            env_cfg=env_cfg
        )
        
        summary = {
            "row_count": len(sample_rows),
            "sum_valor_mensal_final": 22350.00,
            "display_columns": list(sample_rows[0].keys()) if sample_rows else []
        }
        
        try:
            html = emailer.render_html(
                unidade=unit_name,
                regiao="PREVIEW",
                ym=month_ref,
                rows=sample_rows,
                summary=summary,
                destinatarios_exibicao="preview@exemplo.com"
            )
            return html
        except Exception as e:
            logger.exception(f"Erro ao renderizar preview: {e}")
            raise TemplateServiceError(f"Erro ao renderizar preview: {e}")
