"""
Model de Projeto WinDev/WebDev/WinDev Mobile.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import IndexModel, ASCENDING


class ProjectStatus(str, Enum):
    """Status do projeto no pipeline."""
    IMPORTING = "importing"
    IMPORTED = "imported"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    CONVERTING = "converting"
    CONVERTED = "converted"
    VALIDATED = "validated"
    EXPORTED = "exported"
    ERROR = "error"


class ProjectConfiguration(BaseModel):
    """Configuração de build do projeto WinDev."""
    name: str
    configuration_id: str
    config_type: int = Field(alias="type")
    generation_directory: Optional[str] = None
    generation_name: Optional[str] = None
    version: Optional[str] = None
    language: int = 15  # 15 = pt-BR
    is_64bits: bool = Field(default=True, alias="64bits")
    is_linux: bool = Field(default=False, alias="linux")
    excluded: bool = False

    class Config:
        populate_by_name = True


class Project(Document):
    """
    Representa um projeto WinDev/WebDev/WinDev Mobile importado.

    Armazena metadados do projeto e configurações de build.
    Os elementos do projeto são armazenados separadamente na collection 'elements'.
    """

    # Identificacao
    name: str = Field(..., description="Nome do projeto (com sufixo workspace_id para unicidade)")
    display_name: Optional[str] = Field(
        default=None,
        description="Nome original do projeto para exibicao na UI"
    )
    source_path: str = Field(..., description="Caminho do arquivo .wwp/.wdp/.wpp original")
    workspace_id: Optional[str] = Field(
        default=None,
        description="ID do workspace (8 caracteres hex)"
    )
    workspace_path: Optional[str] = Field(
        default=None,
        description="Caminho completo do diretorio do workspace"
    )

    # Versão WinDev
    major_version: int = Field(default=26, description="Versão principal do WinDev")
    minor_version: int = Field(default=0, description="Versão secundária")
    project_type: int = Field(default=4097, description="Tipo do projeto (4097 = WebDev)")

    # Análise (schema do banco)
    analysis_path: Optional[str] = Field(
        default=None,
        description="Caminho do arquivo de análise (.wda)"
    )

    # Configurações de build
    configurations: list[ProjectConfiguration] = Field(
        default_factory=list,
        description="Configurações de build (Produção, Homolog, etc.)"
    )

    # Status
    status: ProjectStatus = Field(
        default=ProjectStatus.IMPORTED,
        description="Status atual do projeto no pipeline"
    )

    # Estatísticas
    total_elements: int = Field(default=0, description="Total de elementos no projeto")
    elements_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Contagem de elementos por tipo"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    analyzed_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None

    # Conversão
    target_stack: Optional[str] = Field(
        default="fastapi-jinja2",
        description="Stack alvo para conversão"
    )

    class Settings:
        name = "projects"
        use_state_management = True
        indexes = [
            IndexModel(
                [("name", ASCENDING)],
                unique=True,
                name="unique_project_name"
            ),
        ]

    def __str__(self) -> str:
        return f"Project({self.name}, v{self.major_version}, status={self.status})"
