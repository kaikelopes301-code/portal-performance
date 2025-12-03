# config.py — Router para gerenciamento de configurações

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.schemas.config import (
    ConfigResponse,
    ConfigUpdateRequest,
    UnitConfigUpdateRequest,
    CopyTexts,
    DefaultsConfig
)
from app.services.config_service import ConfigService, ConfigServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])

# Instância do serviço (singleton)
_config_service = ConfigService()


@router.get("/", response_model=ConfigResponse)
def get_config():
    """
    Retorna todas as configurações do sistema.
    
    Inclui:
    - defaults: Configurações padrão
    - regions: Configurações por região
    - units: Configurações por unidade
    """
    try:
        config = _config_service.get_config()
        return config
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/", response_model=ConfigResponse)
def update_config(request: ConfigUpdateRequest):
    """
    Atualiza configurações do sistema.
    
    Aceita atualizações parciais - apenas os campos fornecidos serão atualizados.
    Cria backup automático antes de salvar.
    """
    try:
        updates = request.model_dump(exclude_none=True)
        config = _config_service.update_config(updates)
        return config
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/defaults")
def get_defaults():
    """Retorna apenas as configurações padrão."""
    try:
        config = _config_service.get_config()
        return config.get("defaults", {})
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/defaults")
def update_defaults(request: DefaultsConfig):
    """Atualiza configurações padrão."""
    try:
        updates = {"defaults": request.model_dump(exclude_none=True)}
        config = _config_service.update_config(updates)
        return config.get("defaults", {})
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ UNITS ============

@router.get("/units")
def list_units():
    """Lista todas as unidades com configurações personalizadas."""
    try:
        units = _config_service.list_units()
        config = _config_service.get_config()
        return {
            "units": units,
            "count": len(units),
            "configs": config.get("units", {})
        }
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/units/{unit_name}")
def get_unit_config(unit_name: str):
    """Retorna configuração de uma unidade específica."""
    try:
        unit_config = _config_service.get_unit_config(unit_name)
        if unit_config is None:
            raise HTTPException(status_code=404, detail=f"Unidade '{unit_name}' não possui configuração personalizada")
        return unit_config
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/units/{unit_name}")
def update_unit_config(unit_name: str, request: UnitConfigUpdateRequest):
    """
    Atualiza ou cria configuração de uma unidade.
    
    Aceita atualizações parciais.
    """
    try:
        updates = request.model_dump(exclude_none=True)
        _config_service.update_unit_config(unit_name, updates)
        return _config_service.get_unit_config(unit_name)
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/units/{unit_name}")
def delete_unit_config(unit_name: str):
    """Remove configuração personalizada de uma unidade."""
    try:
        deleted = _config_service.delete_unit_config(unit_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Unidade '{unit_name}' não encontrada")
        return {"message": f"Configuração de '{unit_name}' removida com sucesso"}
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/units/{unit_name}/effective")
def get_unit_effective_config(
    unit_name: str,
    region: Optional[str] = Query(None, description="Código da região para merge")
):
    """
    Retorna configuração efetiva de uma unidade.
    
    A configuração efetiva é o resultado do merge:
    defaults → região (se informada) → unidade
    """
    try:
        effective = _config_service.get_effective_config(unit_name, region)
        return effective
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ REGIONS ============

@router.get("/regions")
def list_regions():
    """Lista todas as regiões com configurações personalizadas."""
    try:
        regions = _config_service.list_regions()
        config = _config_service.get_config()
        return {
            "regions": regions,
            "count": len(regions),
            "configs": config.get("regions", {})
        }
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/regions/{region_code}")
def get_region_config(region_code: str):
    """Retorna configuração de uma região específica."""
    try:
        region_config = _config_service.get_region_config(region_code)
        if region_config is None:
            raise HTTPException(status_code=404, detail=f"Região '{region_code}' não possui configuração personalizada")
        return region_config
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/regions/{region_code}")
def update_region_config(region_code: str, request: UnitConfigUpdateRequest):
    """
    Atualiza ou cria configuração de uma região.
    
    Aceita atualizações parciais.
    """
    try:
        updates = request.model_dump(exclude_none=True)
        _config_service.update_region_config(region_code, updates)
        return _config_service.get_region_config(region_code)
    except ConfigServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ COLUMNS ============

@router.get("/columns/available")
def get_available_columns():
    """
    Retorna lista de colunas disponíveis para configuração.
    
    Inclui colunas padrão e opcionais.
    """
    return {
        "standard": [
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
            "Mês referência para faturamento",
            "Mês de emissão da NF"
        ],
        "optional": [
            "Desconto SLA Retroativo",
            "Desconto Equipamentos",
            "Prêmio Assiduidade",
            "Outros descontos",
            "Taxa de prorrogação do prazo pagamento",
            "Valor mensal com prorrogação do prazo pagamento",
            "Retroativo de dissídio",
            "Parcela (x/x)",
            "Valor extras validado Atlas"
        ]
    }

