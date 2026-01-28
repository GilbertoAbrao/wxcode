"""
Model de Produto derivado de um projeto.

Representa outputs de um projeto importado: conversao, api, mcp, agents.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from beanie import Document, Indexed, Link
from pydantic import Field

from wxcode.models.project import Project


class ProductType(str, Enum):
    """Tipos de produtos que podem ser gerados de um projeto."""
    CONVERSION = "conversion"
    API = "api"
    MCP = "mcp"
    AGENTS = "agents"


class ProductStatus(str, Enum):
    """Status do ciclo de vida de um produto."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class Product(Document):
    """
    Representa um produto derivado de um projeto WinDev.

    Produtos sao outputs de um projeto importado, como uma conversao
    para FastAPI, uma API REST, um servidor MCP, ou agentes.
    """

    # Relacionamento
    project_id: Link[Project] = Field(..., description="Projeto de origem")

    # Tipo e configuracao
    product_type: ProductType = Field(..., description="Tipo do produto")
    workspace_path: str = Field(..., description="Caminho do workspace do produto")

    # Status
    status: ProductStatus = Field(
        default=ProductStatus.PENDING,
        description="Status atual do produto"
    )

    # Sessao e output
    session_id: Optional[str] = Field(
        default=None,
        description="ID da sessao de processamento (Claude Code, etc.)"
    )
    output_directory: Optional[str] = Field(
        default=None,
        description="Diretorio de saida do produto gerado"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(
        default=None,
        description="Quando o processamento iniciou"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Quando o processamento completou"
    )

    class Settings:
        name = "products"
        use_state_management = True
        indexes = [
            "project_id",
            "product_type",
            "status",
            [("project_id", 1), ("product_type", 1)],
        ]

    def __str__(self) -> str:
        return f"Product({self.product_type.value}, status={self.status.value})"
