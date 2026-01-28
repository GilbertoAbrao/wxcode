"""
API para Tree do Workspace.

Retorna estrutura hierárquica do projeto por configuração:
- Project (raiz)
  - Analysis (schema)
  - Configurations (elementos agrupados por tipo)
"""

from enum import Enum
from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from wxcode.services.tree_builder import TreeBuilder


router = APIRouter()


class TreeNodeType(str, Enum):
    """Tipos de nó na árvore do workspace."""
    PROJECT = "project"
    CONFIGURATION = "configuration"
    ANALYSIS = "analysis"
    CATEGORY = "category"        # Pages, Procedures, Classes, etc.
    ELEMENT = "element"          # PAGE, PROCEDURE_GROUP, CLASS
    PROCEDURE = "procedure"      # Individual procedure
    METHOD = "method"            # Class method
    PROPERTY = "property"        # Class property/member
    TABLE = "table"              # Database table
    QUERY = "query"              # Database query
    CONNECTION = "connection"    # Database connection


class TreeNodeMetadata(BaseModel):
    """Metadados opcionais do nó."""
    config_id: Optional[str] = None
    element_id: Optional[str] = None
    configurations: list[str] = Field(default_factory=list)
    # Para procedures/methods
    parameters_count: Optional[int] = None
    return_type: Optional[str] = None
    is_local: Optional[bool] = None
    # Para tables
    columns_count: Optional[int] = None
    # Para classes
    members_count: Optional[int] = None
    methods_count: Optional[int] = None


class TreeNodeResponse(BaseModel):
    """Resposta de um nó da árvore."""
    id: str = Field(..., description="ID único do nó")
    name: str = Field(..., description="Nome para exibição")
    node_type: TreeNodeType = Field(..., description="Tipo do nó")
    element_type: Optional[str] = Field(
        default=None,
        description="Tipo do elemento WinDev (page, procedure_group, class, etc.)"
    )
    status: Optional[str] = Field(
        default=None,
        description="Status de conversão"
    )
    icon: Optional[str] = Field(
        default=None,
        description="Nome do ícone sugerido"
    )
    has_children: bool = Field(..., description="Se o nó tem filhos")
    children_count: int = Field(default=0, description="Quantidade de filhos")
    children: Optional[list["TreeNodeResponse"]] = Field(
        default=None,
        description="Filhos carregados (lazy loading)"
    )
    metadata: Optional[TreeNodeMetadata] = Field(
        default=None,
        description="Metadados adicionais"
    )

    class Config:
        from_attributes = True


# Resolve forward reference
TreeNodeResponse.model_rebuild()


@router.get("/{project_id}", response_model=TreeNodeResponse)
async def get_project_tree(
    project_id: str,
    depth: int = Query(default=1, ge=1, le=4, description="Profundidade inicial da árvore")
) -> TreeNodeResponse:
    """
    Retorna a árvore do projeto com profundidade especificada.

    Args:
        project_id: ID do projeto
        depth: Profundidade inicial (1-4). Default=1 carrega apenas nível raiz.

    Returns:
        Nó raiz do projeto com filhos até a profundidade especificada.
    """
    try:
        oid = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de projeto inválido")

    builder = TreeBuilder()
    tree = await builder.build_project_tree(oid, depth=depth)

    if tree is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return tree


@router.get("/{project_id}/node/{node_id}/children", response_model=list[TreeNodeResponse])
async def get_node_children(
    project_id: str,
    node_id: str,
    node_type: TreeNodeType = Query(..., description="Tipo do nó pai")
) -> list[TreeNodeResponse]:
    """
    Carrega filhos de um nó (lazy loading).

    O node_id pode ser:
    - ID de configuração (para node_type=configuration)
    - Nome de categoria (para node_type=category, ex: "pages", "procedures")
    - ID de elemento (para node_type=element)

    Args:
        project_id: ID do projeto
        node_id: ID ou identificador do nó pai
        node_type: Tipo do nó pai

    Returns:
        Lista de nós filhos.
    """
    try:
        project_oid = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de projeto inválido")

    builder = TreeBuilder()

    if node_type == TreeNodeType.CONFIGURATION:
        return await builder.expand_configuration(project_oid, node_id)

    elif node_type == TreeNodeType.ANALYSIS:
        return await builder.expand_analysis(project_oid)

    elif node_type == TreeNodeType.CATEGORY:
        # node_id format: "config_id:category_name" ou apenas "category_name" para analysis
        if ":" in node_id:
            config_id, category = node_id.split(":", 1)
        else:
            config_id = None
            category = node_id
        return await builder.expand_category(project_oid, config_id, category)

    elif node_type == TreeNodeType.ELEMENT:
        try:
            element_oid = PydanticObjectId(node_id)
        except Exception:
            raise HTTPException(status_code=400, detail="ID de elemento inválido")
        return await builder.expand_element(element_oid)

    else:
        # Outros tipos não têm lazy loading de filhos
        return []
