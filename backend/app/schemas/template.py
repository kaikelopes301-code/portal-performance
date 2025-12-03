# template.py — Schemas para templates de email

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TemplateBase(BaseModel):
    """Base para template de email."""
    name: str = Field(..., description="Nome identificador do template")
    description: Optional[str] = Field(None, description="Descrição do template")
    subject_template: str = Field(..., description="Template do assunto do email")
    is_active: bool = Field(True, description="Se o template está ativo")


class TemplateCreate(TemplateBase):
    """Schema para criação de template."""
    content: str = Field(..., description="Conteúdo HTML do template")


class TemplateUpdate(BaseModel):
    """Schema para atualização de template."""
    name: Optional[str] = None
    description: Optional[str] = None
    subject_template: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    """Schema de resposta de template."""
    id: str
    filename: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TemplatePreviewRequest(BaseModel):
    """Request para preview de template."""
    template_id: str = Field(..., description="ID do template")
    unit_name: str = Field("Shopping Exemplo", description="Nome da unidade para preview")
    month_ref: str = Field("2025-11", description="Mês de referência")
    sample_data: Optional[List[dict]] = Field(None, description="Dados de exemplo para preview")


class TemplateListResponse(BaseModel):
    """Resposta da listagem de templates."""
    templates: List[TemplateResponse]
    count: int
