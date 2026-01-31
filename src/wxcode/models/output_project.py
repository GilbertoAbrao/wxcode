"""
Model de OutputProject para projetos de conversao.

Representa um projeto de saida que converte elementos de um Knowledge Base
para uma stack alvo.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field


class OutputProjectStatus(str, Enum):
    """Status do ciclo de vida de um OutputProject."""
    CREATED = "created"
    INITIALIZED = "initialized"
    ACTIVE = "active"


class OutputProjectConnection(BaseModel):
    """
    Connection de banco para OutputProject.

    Replica connections da KB (editaveis) e adiciona connection SQLite dev (nao editavel).
    """

    # Campos herdados de SchemaConnection
    name: str = Field(..., description="Nome da conexao (ex: CNX_BASE_HOMOLOG)")
    type_code: int = Field(default=0, description="Tipo de conexao (1 = SQL Server)")
    database_type: str = Field(..., description="Tipo do banco (sqlserver, sqlite, etc.)")
    driver_name: str = Field(default="", description="Nome legivel do driver")
    source: str = Field(default="", description="Servidor/host ou path do arquivo")
    port: str = Field(default="", description="Porta da conexao")
    database: str = Field(default="", description="Nome do banco de dados")
    user: Optional[str] = Field(default=None, description="Usuario da conexao")

    # Campos especificos do OutputProject
    is_editable: bool = Field(
        default=True,
        description="Se pode ser editada pelo usuario (False para SQLite dev)"
    )
    is_dev_connection: bool = Field(
        default=False,
        description="Se e a connection de desenvolvimento local (True para SQLite dev)"
    )
    connection_string: Optional[str] = Field(
        default=None,
        description="SQLAlchemy connection string"
    )

    # Origem
    source_connection_name: Optional[str] = Field(
        default=None,
        description="Nome original da conexao na KB (se replicada)"
    )


class OutputProject(Document):
    """
    Representa um projeto de conversao de elementos KB para uma stack alvo.

    OutputProject connects a Knowledge Base (Project) with a target Stack,
    and tracks the workspace where Claude Code generates the converted code.
    """

    # Referencias (using PydanticObjectId to avoid extra queries)
    kb_id: PydanticObjectId = Field(
        ...,
        description="Reference to Knowledge Base (Project)"
    )

    # Identificacao
    name: str = Field(
        ...,
        description="User-defined project name"
    )

    # Stack alvo
    stack_id: str = Field(
        ...,
        description="Reference to Stack.stack_id"
    )

    # Configuracao WinDev (opcional)
    configuration_id: Optional[str] = Field(
        default=None,
        description="Selected WinDev Configuration ID, can be None"
    )

    # Workspace
    workspace_path: str = Field(
        ...,
        description="Path in ~/.wxcode/workspaces/"
    )

    # Status
    status: OutputProjectStatus = Field(
        default=OutputProjectStatus.CREATED,
        description="Current status: created | initialized | active"
    )

    # Session persistence for Claude Code
    claude_session_id: Optional[str] = Field(
        default=None,
        description="Claude Code session_id for conversation resume"
    )

    # Database connections
    connections: list[OutputProjectConnection] = Field(
        default_factory=list,
        description="Database connections for this project"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "output_projects"
        use_state_management = True
        indexes = [
            "kb_id",
            "stack_id",
            "status",
            [("kb_id", 1), ("stack_id", 1)],
            [("kb_id", 1), ("status", 1)],
        ]

    def __str__(self) -> str:
        return f"OutputProject({self.name}, stack={self.stack_id}, status={self.status.value})"
