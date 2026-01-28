"""
API de Elementos.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from wxcode.models import Element, ElementType, ElementLayer, ConversionStatus


router = APIRouter()


class ElementResponse(BaseModel):
    """Resposta de elemento."""
    id: str
    source_type: ElementType
    source_name: str
    source_file: str
    layer: Optional[ElementLayer]
    topological_order: Optional[int]
    conversion_status: ConversionStatus
    has_chunks: bool
    dependencies_count: int  # Quantidade de elementos que este USA
    dependents_count: int  # Quantidade de elementos que USAM este
    dependencies_uses: list[str]  # Nomes dos elementos que este usa

    class Config:
        from_attributes = True


class ElementDetailResponse(ElementResponse):
    """Resposta detalhada de elemento."""
    raw_content: str
    dependencies_uses: list[str]
    dependencies_used_by: list[str]


class ElementListResponse(BaseModel):
    """Lista de elementos."""
    elements: list[ElementResponse]
    total: int


@router.get("/", response_model=ElementListResponse)
async def list_elements(
    project_name: Optional[str] = Query(None, description="Nome do projeto"),
    project_id: Optional[str] = Query(None, description="ID do projeto"),
    source_type: Optional[ElementType] = None,
    layer: Optional[ElementLayer] = None,
    status: Optional[ConversionStatus] = None,
    skip: int = 0,
    limit: int = 100,
) -> ElementListResponse:
    """Lista elementos de um projeto."""
    from wxcode.models import Project
    from beanie import PydanticObjectId

    # Busca projeto por ID ou nome
    project = None
    if project_id:
        try:
            project = await Project.get(PydanticObjectId(project_id))
        except Exception:
            raise HTTPException(status_code=400, detail="project_id inválido")
    elif project_name:
        project = await Project.find_one(Project.name == project_name)
    else:
        raise HTTPException(status_code=400, detail="Informe project_name ou project_id")

    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    # Monta query - Link fields são armazenados como DBRef, precisa usar $id
    query = Element.find({"project_id.$id": project.id})

    if source_type:
        query = query.find(Element.source_type == source_type)
    if layer:
        query = query.find(Element.layer == layer)
    if status:
        query = query.find(Element.conversion.status == status)

    # Executa
    elements = await query.skip(skip).limit(limit).to_list()
    total = await query.count()

    return ElementListResponse(
        elements=[
            ElementResponse(
                id=str(e.id),
                source_type=e.source_type,
                source_name=e.source_name,
                source_file=e.source_file,
                layer=e.layer,
                topological_order=e.topological_order,
                conversion_status=e.conversion.status,
                has_chunks=len(e.chunks) > 0,
                dependencies_count=len(e.dependencies.uses),
                dependents_count=len(e.dependencies.used_by),
                dependencies_uses=e.dependencies.uses,
            )
            for e in elements
        ],
        total=total,
    )


async def _load_raw_content_if_empty(element: Element) -> str:
    """Carrega raw_content do arquivo se estiver vazio."""
    if element.raw_content:
        return element.raw_content

    # Tenta carregar do arquivo fonte
    from pathlib import Path
    from wxcode.models import Project

    project = await Project.get(element.project_id.ref.id)
    if not project:
        return ""

    # Tenta encontrar o arquivo no project-refs
    project_refs_dir = Path("./project-refs") / project.name
    # Remove prefixos como ".\" ou "./"
    clean_source_file = element.source_file.lstrip("./\\")
    source_file = project_refs_dir / clean_source_file

    if source_file.exists():
        try:
            content = source_file.read_text(encoding='utf-8', errors='replace')
            # Atualiza o elemento para não precisar ler novamente
            element.raw_content = content
            await element.save()
            return content
        except Exception as e:
            print(f"Erro ao carregar raw_content de {source_file}: {e}")
            return ""

    return ""


@router.get("/{element_id}", response_model=ElementDetailResponse)
async def get_element(element_id: str) -> ElementDetailResponse:
    """Busca um elemento por ID."""
    element = await Element.get(element_id)
    if not element:
        raise HTTPException(status_code=404, detail="Elemento não encontrado")

    # Carrega raw_content on-demand se estiver vazio
    raw_content = await _load_raw_content_if_empty(element)

    return ElementDetailResponse(
        id=str(element.id),
        source_type=element.source_type,
        source_name=element.source_name,
        source_file=element.source_file,
        layer=element.layer,
        topological_order=element.topological_order,
        conversion_status=element.conversion.status,
        has_chunks=len(element.chunks) > 0,
        dependencies_count=len(element.dependencies.uses),
        dependents_count=len(element.dependencies.used_by),
        raw_content=raw_content,
        dependencies_uses=element.dependencies.uses,
        dependencies_used_by=element.dependencies.used_by,
    )


@router.get("/by-name/{project_name}/{element_name}", response_model=ElementDetailResponse)
async def get_element_by_name(project_name: str, element_name: str) -> ElementDetailResponse:
    """Busca um elemento por nome."""
    from wxcode.models import Project

    project = await Project.find_one(Project.name == project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    element = await Element.find_one(
        Element.project_id == project.id,
        Element.source_name == element_name,
    )
    if not element:
        raise HTTPException(status_code=404, detail="Elemento não encontrado")

    # Carrega raw_content on-demand se estiver vazio
    raw_content = await _load_raw_content_if_empty(element)

    return ElementDetailResponse(
        id=str(element.id),
        source_type=element.source_type,
        source_name=element.source_name,
        source_file=element.source_file,
        layer=element.layer,
        topological_order=element.topological_order,
        conversion_status=element.conversion.status,
        has_chunks=len(element.chunks) > 0,
        dependencies_count=len(element.dependencies.uses),
        dependents_count=len(element.dependencies.used_by),
        raw_content=raw_content,
        dependencies_uses=element.dependencies.uses,
        dependencies_used_by=element.dependencies.used_by,
    )
