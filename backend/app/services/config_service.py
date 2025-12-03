# config_service.py — Serviço de gerenciamento de configurações

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # backpperformance/
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "overrides.json"
BACKUP_DIR = CONFIG_DIR / "backups"

# Garante que diretórios existem
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


class ConfigServiceError(Exception):
    """Erro no serviço de configuração."""
    pass


class ConfigService:
    """
    Serviço para gerenciamento de configurações do sistema.
    
    As configurações são persistidas em JSON no disco.
    Suporta:
    - Configurações padrão (defaults)
    - Configurações por região
    - Configurações por unidade (override)
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_time: Optional[datetime] = None
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão se o arquivo não existir."""
        return {
            "defaults": {
                "visible_columns": [
                    "Unidade",
                    "Categoria",
                    "Fornecedor",
                    "HC Planilha",
                    "Dias Faltas",
                    "Horas Atrasos",
                    "Valor Planilha",
                    "Desc. Falta Validado Atlas",
                    "Desc. Atraso Validado Atlas",
                    "Desconto SLA Mês",
                    "Valor Mensal Final",
                    "Mês de emissão da NF"
                ],
                "copy": {
                    "greeting": "Prezados(as),",
                    "intro": "Encaminhamos a medição mensal referente à {{ unidade }}.",
                    "observation": "Observação: caso a Nota Fiscal já tenha sido emitida sem considerar os descontos ora apontados, os valores poderão ser objeto de desconto retroativo na competência subsequente.",
                    "cta_label": "Preencher SLA",
                    "footer_signature": "Atenciosamente,<br>{{ sender_name }}",
                    "subject_template": "Medição {unidade} - {mes_ref}"
                },
                "month_reference": "auto"
            },
            "regions": {},
            "units": {}
        }
    
    def _load_from_disk(self) -> Dict[str, Any]:
        """Carrega configuração do disco."""
        if not self.config_path.exists():
            logger.info(f"Arquivo de configuração não existe, criando padrão: {self.config_path}")
            default_config = self._get_default_config()
            self._save_to_disk(default_config)
            return default_config
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Garante estrutura mínima
            if "defaults" not in config:
                config["defaults"] = self._get_default_config()["defaults"]
            if "regions" not in config:
                config["regions"] = {}
            if "units" not in config:
                config["units"] = {}
            
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao parsear JSON de configuração: {e}")
            raise ConfigServiceError(f"Arquivo de configuração corrompido: {e}")
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            raise ConfigServiceError(f"Erro ao carregar configuração: {e}")
    
    def _save_to_disk(self, config: Dict[str, Any]) -> None:
        """Salva configuração no disco com backup."""
        try:
            # Cria backup se arquivo existe
            if self.config_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = BACKUP_DIR / f"overrides_{timestamp}.json"
                shutil.copy2(self.config_path, backup_path)
                logger.info(f"Backup criado: {backup_path}")
                
                # Mantém apenas últimos 10 backups
                backups = sorted(BACKUP_DIR.glob("overrides_*.json"), reverse=True)
                for old_backup in backups[10:]:
                    old_backup.unlink()
            
            # Salva nova configuração
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            # Invalida cache
            self._cache = None
            self._cache_time = None
            
            logger.info(f"Configuração salva: {self.config_path}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {e}")
            raise ConfigServiceError(f"Erro ao salvar configuração: {e}")
    
    def get_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Retorna configuração completa.
        
        Args:
            use_cache: Se True, usa cache em memória (invalida após 60s)
        """
        # Verifica cache
        if use_cache and self._cache is not None:
            if self._cache_time and (datetime.now() - self._cache_time).seconds < 60:
                return self._cache
        
        config = self._load_from_disk()
        self._cache = config
        self._cache_time = datetime.now()
        
        return config
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza configuração com merge parcial.
        
        Args:
            updates: Dicionário com atualizações (pode ser parcial)
        
        Returns:
            Configuração atualizada completa
        """
        config = self.get_config(use_cache=False)
        
        # Merge de defaults
        if "defaults" in updates and updates["defaults"]:
            defaults_update = updates["defaults"]
            if isinstance(defaults_update, dict):
                for key, value in defaults_update.items():
                    if value is not None:
                        if key == "copy" and isinstance(value, dict):
                            # Merge de copy (não substitui tudo)
                            if "copy" not in config["defaults"]:
                                config["defaults"]["copy"] = {}
                            for copy_key, copy_value in value.items():
                                if copy_value is not None:
                                    config["defaults"]["copy"][copy_key] = copy_value
                        else:
                            config["defaults"][key] = value
        
        # Merge de regions
        if "regions" in updates and updates["regions"]:
            for region_code, region_config in updates["regions"].items():
                if region_config is None:
                    # Remove região
                    config["regions"].pop(region_code, None)
                else:
                    if region_code not in config["regions"]:
                        config["regions"][region_code] = {}
                    self._merge_override(config["regions"][region_code], region_config)
        
        # Merge de units
        if "units" in updates and updates["units"]:
            for unit_name, unit_config in updates["units"].items():
                if unit_config is None:
                    # Remove unidade
                    config["units"].pop(unit_name, None)
                else:
                    if unit_name not in config["units"]:
                        config["units"][unit_name] = {}
                    self._merge_override(config["units"][unit_name], unit_config)
        
        self._save_to_disk(config)
        return config
    
    def _merge_override(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Faz merge de override preservando valores existentes."""
        if isinstance(source, dict):
            source_dict = source
        else:
            # Pydantic model
            source_dict = source.dict(exclude_none=True) if hasattr(source, 'dict') else dict(source)
        
        for key, value in source_dict.items():
            if value is not None:
                if key == "copy" and isinstance(value, dict):
                    if "copy" not in target:
                        target["copy"] = {}
                    for copy_key, copy_value in value.items():
                        if copy_value is not None:
                            target["copy"][copy_key] = copy_value
                else:
                    target[key] = value
    
    def get_unit_config(self, unit_name: str) -> Optional[Dict[str, Any]]:
        """Retorna configuração de uma unidade específica."""
        config = self.get_config()
        return config.get("units", {}).get(unit_name)
    
    def update_unit_config(self, unit_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza configuração de uma unidade específica."""
        return self.update_config({
            "units": {
                unit_name: updates
            }
        })
    
    def delete_unit_config(self, unit_name: str) -> bool:
        """Remove configuração de uma unidade."""
        config = self.get_config(use_cache=False)
        if unit_name in config.get("units", {}):
            del config["units"][unit_name]
            self._save_to_disk(config)
            return True
        return False
    
    def get_region_config(self, region_code: str) -> Optional[Dict[str, Any]]:
        """Retorna configuração de uma região específica."""
        config = self.get_config()
        return config.get("regions", {}).get(region_code)
    
    def update_region_config(self, region_code: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza configuração de uma região específica."""
        return self.update_config({
            "regions": {
                region_code: updates
            }
        })
    
    def get_effective_config(self, unit_name: str, region_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Retorna configuração efetiva para uma unidade (com merge de defaults + região + unidade).
        
        A ordem de prioridade é:
        1. Configuração da unidade (maior prioridade)
        2. Configuração da região
        3. Configuração padrão (menor prioridade)
        """
        config = self.get_config()
        
        # Começa com defaults
        effective = {
            "visible_columns": config["defaults"].get("visible_columns", []).copy(),
            "copy": config["defaults"].get("copy", {}).copy(),
            "month_reference": config["defaults"].get("month_reference", "auto"),
            "recipients": []
        }
        
        # Aplica override de região
        if region_code and region_code in config.get("regions", {}):
            region_cfg = config["regions"][region_code]
            if region_cfg.get("visible_columns"):
                effective["visible_columns"] = region_cfg["visible_columns"].copy()
            if region_cfg.get("copy"):
                effective["copy"].update(region_cfg["copy"])
            if region_cfg.get("month_reference"):
                effective["month_reference"] = region_cfg["month_reference"]
        
        # Aplica override de unidade
        if unit_name in config.get("units", {}):
            unit_cfg = config["units"][unit_name]
            if unit_cfg.get("visible_columns"):
                effective["visible_columns"] = unit_cfg["visible_columns"].copy()
            if unit_cfg.get("copy"):
                effective["copy"].update(unit_cfg["copy"])
            if unit_cfg.get("month_reference"):
                effective["month_reference"] = unit_cfg["month_reference"]
            if unit_cfg.get("recipients"):
                effective["recipients"] = unit_cfg["recipients"].copy()
        
        return effective
    
    def list_units(self) -> list:
        """Lista todas as unidades com configurações personalizadas."""
        config = self.get_config()
        return list(config.get("units", {}).keys())
    
    def list_regions(self) -> list:
        """Lista todas as regiões com configurações personalizadas."""
        config = self.get_config()
        return list(config.get("regions", {}).keys())
