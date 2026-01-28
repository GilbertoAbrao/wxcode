"""
Modelo para metadados de workspace.

Workspaces sao diretorios isolados para cada projeto importado,
localizados em ~/.wxcode/workspaces/{project_name}_{id}/.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# Tipos de produtos que podem ser gerados em um workspace
PRODUCT_TYPES: list[str] = ["conversion", "api", "mcp", "agents"]


class WorkspaceMetadata(BaseModel):
    """
    Metadados do workspace armazenados em .workspace.json.

    Cada workspace tem um arquivo .workspace.json na raiz que contem
    informacoes sobre quando foi criado e de onde veio o projeto.
    """

    workspace_id: str = Field(
        ...,
        description="Identificador unico de 8 caracteres hex (secrets.token_hex(4))"
    )
    project_name: str = Field(
        ...,
        description="Nome original do projeto (nao sanitizado)"
    )
    created_at: datetime = Field(
        ...,
        description="Data/hora de criacao do workspace (UTC)"
    )
    imported_from: str = Field(
        ...,
        description="Caminho original do arquivo .wwp importado"
    )
