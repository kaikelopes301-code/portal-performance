# templates.py — Router para gerenciamento de templates de email

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Optional, List
import logging

from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    TemplatePreviewRequest
)
from app.services.template_service import TemplateService, TemplateServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])

# Instância do serviço (singleton)
_template_service = TemplateService()


@router.get("/", response_model=TemplateListResponse)
def list_templates():
    """
    Lista todos os templates de email disponíveis.
    """
    try:
        templates = _template_service.list_templates()
        return {
            "templates": templates,
            "count": len(templates)
        }
    except TemplateServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/default")
def get_default_template():
    """Retorna informações do template padrão."""
    try:
        default_id = _template_service.get_default_template()
        template = _template_service.get_template(default_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template padrão não encontrado")
        return template
    except TemplateServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/default/{template_id}")
def set_default_template(template_id: str):
    """Define qual template será o padrão."""
    try:
        _template_service.set_default_template(template_id)
        return {"message": f"Template '{template_id}' definido como padrão"}
    except TemplateServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{template_id}")
def get_template(template_id: str):
    """Retorna metadados de um template específico."""
    try:
        template = _template_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' não encontrado")
        return template
    except TemplateServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/content", response_class=HTMLResponse)
def get_template_content(template_id: str):
    """Retorna o conteúdo HTML do template."""
    try:
        content = _template_service.get_template_content(template_id)
        if not content:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' não encontrado")
        return HTMLResponse(content=content)
    except TemplateServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
def create_template(request: TemplateCreate):
    """
    Cria um novo template de email.
    
    O ID é gerado automaticamente a partir do nome.
    """
    try:
        # Gera ID a partir do nome
        template_id = request.name.lower().replace(" ", "_")
        template_id = "".join(c for c in template_id if c.isalnum() or c == "_")
        
        template = _template_service.create_template(
            template_id=template_id,
            name=request.name,
            content=request.content,
            description=request.description,
            subject_template=request.subject_template
        )
        return template
    except TemplateServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{template_id}")
def update_template(template_id: str, request: TemplateUpdate):
    """
    Atualiza um template existente.
    
    Aceita atualizações parciais.
    """
    try:
        template = _template_service.update_template(
            template_id=template_id,
            name=request.name,
            content=request.content,
            description=request.description,
            subject_template=request.subject_template,
            is_active=request.is_active
        )
        return template
    except TemplateServiceError as e:
        if "não encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{template_id}")
def delete_template(template_id: str):
    """
    Remove um template.
    
    O template padrão não pode ser removido.
    """
    try:
        deleted = _template_service.delete_template(template_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Template '{template_id}' não encontrado")
        return {"message": f"Template '{template_id}' removido com sucesso"}
    except TemplateServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/preview", response_class=HTMLResponse)
def preview_template(
    template_id: str,
    unit_name: str = "Shopping Exemplo",
    month_ref: str = "2025-11"
):
    """
    Gera preview de um template com dados de exemplo.
    
    Útil para visualizar como o template ficará com dados reais.
    """
    try:
        html = _template_service.preview_template(
            template_id=template_id,
            unit_name=unit_name,
            month_ref=month_ref
        )
        return HTMLResponse(content=html)
    except TemplateServiceError as e:
        if "não encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}/preview", response_class=HTMLResponse)
def preview_template_get(
    template_id: str,
    unit_name: str = "Shopping Exemplo",
    month_ref: str = "2025-11"
):
    """
    Gera preview de um template (GET).
    
    Versão GET para facilitar acesso via browser.
    """
    try:
        html = _template_service.preview_template(
            template_id=template_id,
            unit_name=unit_name,
            month_ref=month_ref
        )
        return HTMLResponse(content=html)
    except TemplateServiceError as e:
        if "não encontrado" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
