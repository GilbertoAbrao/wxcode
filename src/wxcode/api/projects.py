"""
API de Projetos.
"""

from typing import Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from wxcode.models import Project, ProjectStatus, ProjectConfiguration
from wxcode.services import purge_project, PurgeStats


router = APIRouter()


class ProjectResponse(BaseModel):
    """Resposta de projeto."""

    id: str
    name: str
    display_name: Optional[str] = None
    major_version: int
    minor_version: int
    status: ProjectStatus
    total_elements: int
    elements_by_type: dict[str, int]
    configurations: list[ProjectConfiguration] = []

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """Lista de projetos."""

    projects: list[ProjectResponse]
    total: int


class DeleteProjectResponse(BaseModel):
    """Resposta de remoção de projeto com estatísticas."""

    message: str
    stats: dict[str, int]


@router.get("", response_model=ProjectListResponse, include_in_schema=False)
@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
) -> ProjectListResponse:
    """Lista todos os projetos."""
    projects = await Project.find_all().skip(skip).limit(limit).to_list()
    total = await Project.count()

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                id=str(p.id),
                name=p.name,
                display_name=p.display_name,
                major_version=p.major_version,
                minor_version=p.minor_version,
                status=p.status,
                total_elements=p.total_elements,
                elements_by_type=p.elements_by_type,
                configurations=p.configurations,
            )
            for p in projects
        ],
        total=total,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    """Busca um projeto por ID."""
    project = await Project.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        display_name=project.display_name,
        major_version=project.major_version,
        minor_version=project.minor_version,
        status=project.status,
        total_elements=project.total_elements,
        elements_by_type=project.elements_by_type,
        configurations=project.configurations,
    )


@router.get("/by-name/{name}", response_model=ProjectResponse)
async def get_project_by_name(name: str) -> ProjectResponse:
    """Busca um projeto por nome."""
    project = await Project.find_one(Project.name == name)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        display_name=project.display_name,
        major_version=project.major_version,
        minor_version=project.minor_version,
        status=project.status,
        total_elements=project.total_elements,
        elements_by_type=project.elements_by_type,
        configurations=project.configurations,
    )


@router.delete("/{project_id}", response_model=DeleteProjectResponse)
async def delete_project(project_id: str) -> DeleteProjectResponse:
    """
    Remove um projeto e todos os seus dados do banco.

    Remove todas as collections dependentes:
    - elements (elementos do projeto)
    - controls (controles de UI)
    - procedures (procedures globais e locais)
    - class_definitions (classes)
    - schemas (schema do banco)
    - conversions (conversões realizadas)

    Returns:
        Mensagem de sucesso com estatísticas de remoção
    """
    try:
        object_id = PydanticObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID de projeto inválido")

    try:
        stats = await purge_project(object_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return DeleteProjectResponse(
        message=f"Projeto '{stats.project_name}' removido com sucesso",
        stats=stats.to_dict(),
    )
