# config.py — Schemas para configurações do sistema

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class CopyTexts(BaseModel):
    """Textos personalizáveis dos emails."""
    greeting: Optional[str] = Field(None, description="Saudação inicial do email")
    intro: Optional[str] = Field(None, description="Texto de introdução")
    observation: Optional[str] = Field(None, description="Texto de observação")
    cta_label: Optional[str] = Field(None, description="Texto do botão CTA")
    footer_signature: Optional[str] = Field(None, description="Assinatura do rodapé")
    subject_template: Optional[str] = Field(None, description="Template do assunto do email")


class SenderConfig(BaseModel):
    """Configurações do remetente."""
    name: str = Field(..., description="Nome de exibição do remetente")
    email: str = Field(..., description="Email do remetente")


class EmailConfig(BaseModel):
    """Configurações gerais de email."""
    sender: SenderConfig
    sla_url: Optional[str] = Field(None, description="URL do formulário SLA")
    copy_texts: CopyTexts = Field(..., alias="copy")

    class Config:
        populate_by_name = True


class DefaultsConfig(BaseModel):
    """Configurações padrão do sistema."""
    visible_columns: Optional[List[str]] = Field(default=None, description="Colunas visíveis no relatório")
    copy_texts: Optional[CopyTexts] = Field(default=None, alias="copy")
    month_reference: Optional[str] = Field(default="auto", description="Referência de mês (auto, YYYY-MM, ou offset)")

    class Config:
        populate_by_name = True


class RegionConfig(BaseModel):
    """Configurações específicas de uma região."""
    copy_texts: Optional[CopyTexts] = Field(None, alias="copy")
    visible_columns: Optional[List[str]] = None
    month_reference: Optional[str] = None

    class Config:
        populate_by_name = True


class UnitConfig(BaseModel):
    """Configurações específicas de uma unidade."""
    copy_texts: Optional[CopyTexts] = Field(None, alias="copy")
    visible_columns: Optional[List[str]] = None
    month_reference: Optional[str] = None
    recipients: Optional[List[str]] = Field(None, description="Lista de destinatários")

    class Config:
        populate_by_name = True


class AppConfig(BaseModel):
    """Configuração completa do aplicativo."""
    defaults: DefaultsConfig
    regions: Dict[str, RegionConfig] = Field(default_factory=dict)
    units: Dict[str, UnitConfig] = Field(default_factory=dict)


class ConfigResponse(BaseModel):
    """Resposta da API de configuração."""
    defaults: DefaultsConfig
    regions: Dict[str, Any]
    units: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ConfigUpdateRequest(BaseModel):
    """Request para atualização de configuração."""
    defaults: Optional[DefaultsConfig] = None
    regions: Optional[Dict[str, RegionConfig]] = None
    units: Optional[Dict[str, UnitConfig]] = None


class UnitConfigUpdateRequest(BaseModel):
    """Request para atualização de configuração de uma unidade."""
    copy_texts: Optional[CopyTexts] = Field(None, alias="copy")
    visible_columns: Optional[List[str]] = None
    month_reference: Optional[str] = None
    recipients: Optional[List[str]] = None

    class Config:
        populate_by_name = True
