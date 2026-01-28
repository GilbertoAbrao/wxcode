"""
Serviço de gerenciamento de projetos.

Inclui funções para purge completo de projetos e verificação de duplicatas.
"""

import logging
import os
import shutil
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from wxcode.config import get_settings

from beanie import PydanticObjectId

from wxcode.models import (
    Project,
    Element,
    Control,
    Procedure,
    ClassDefinition,
    DatabaseSchema,
    Conversion,
)

logger = logging.getLogger(__name__)


@dataclass
class PurgeStats:
    """Estatísticas de remoção de um purge."""
    project_name: str = ""
    projects: int = 0
    elements: int = 0
    controls: int = 0
    procedures: int = 0
    class_definitions: int = 0
    schemas: int = 0
    conversions: int = 0
    neo4j_nodes: int = 0
    neo4j_error: Optional[str] = None
    files_deleted: int = 0
    directories_deleted: int = 0
    files_error: Optional[str] = None

    @property
    def total(self) -> int:
        """Total de documentos removidos (MongoDB)."""
        return (
            self.projects +
            self.elements +
            self.controls +
            self.procedures +
            self.class_definitions +
            self.schemas +
            self.conversions
        )

    @property
    def total_with_neo4j(self) -> int:
        """Total incluindo nós Neo4j."""
        return self.total + self.neo4j_nodes

    @property
    def total_files(self) -> int:
        """Total de arquivos e diretorios removidos."""
        return self.files_deleted + self.directories_deleted

    def to_dict(self) -> dict:
        """Converte para dicionário."""
        result = {
            "project_name": self.project_name,
            "projects": self.projects,
            "elements": self.elements,
            "controls": self.controls,
            "procedures": self.procedures,
            "class_definitions": self.class_definitions,
            "schemas": self.schemas,
            "conversions": self.conversions,
            "total": self.total,
            "files_deleted": self.files_deleted,
            "directories_deleted": self.directories_deleted,
            "total_files": self.total_files,
        }
        if self.neo4j_nodes > 0:
            result["neo4j_nodes"] = self.neo4j_nodes
        if self.neo4j_error:
            result["neo4j_error"] = self.neo4j_error
        if self.files_error:
            result["files_error"] = self.files_error
        return result


async def purge_project(project_id: PydanticObjectId) -> PurgeStats:
    """
    Remove completamente um projeto e todas suas collections dependentes.

    Args:
        project_id: ID do projeto a ser removido

    Returns:
        PurgeStats com contagem de documentos removidos por collection

    Raises:
        ValueError: Se o projeto não existir
    """
    project = await Project.get(project_id)
    if not project:
        raise ValueError(f"Projeto com ID {project_id} não encontrado")

    return await _purge_project_data(project)


async def purge_project_by_name(project_name: str) -> PurgeStats:
    """
    Remove completamente um projeto pelo nome e todas suas collections dependentes.

    Args:
        project_name: Nome do projeto a ser removido

    Returns:
        PurgeStats com contagem de documentos removidos por collection

    Raises:
        ValueError: Se o projeto não existir
    """
    project = await Project.find_one(Project.name == project_name)
    if not project:
        raise ValueError(f"Projeto '{project_name}' não encontrado")

    return await _purge_project_data(project)


def _remove_readonly(func, path, exc_info):
    """Handler para arquivos read-only (especialmente Windows)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _validate_deletion_path(source_path: str, allowed_base: Path) -> Path:
    """
    Valida que o path esta dentro do diretorio permitido.

    Args:
        source_path: Path do arquivo .wwp do projeto
        allowed_base: Diretorio base permitido para delecao

    Returns:
        Path resolvido do diretorio do projeto (parent do .wwp)

    Raises:
        ValueError: Se path esta fora do diretorio permitido
    """
    wwp_path = Path(source_path).resolve()
    project_dir = wwp_path.parent
    allowed = allowed_base.resolve()

    if not project_dir.is_relative_to(allowed):
        raise ValueError(
            f"Path '{project_dir}' esta fora do diretorio permitido '{allowed}'"
        )

    return project_dir


def _purge_local_files(project_dir: Path, stats: PurgeStats) -> None:
    """
    Remove o diretorio do projeto e todo seu conteudo.

    Similar a _purge_neo4j_data: nao falha se houver erro,
    apenas registra no stats.

    Args:
        project_dir: Path do diretorio do projeto
        stats: PurgeStats para atualizar com contagens
    """
    try:
        if not project_dir.exists():
            logger.debug(f"Diretorio nao existe, pulando: {project_dir}")
            return

        if not project_dir.is_dir():
            stats.files_error = f"Path nao e um diretorio: {project_dir}"
            logger.warning(stats.files_error)
            return

        # Conta antes de deletar
        stats.files_deleted = sum(1 for p in project_dir.rglob("*") if p.is_file())
        stats.directories_deleted = sum(1 for p in project_dir.rglob("*") if p.is_dir()) + 1

        # Deleta com handler para read-only
        shutil.rmtree(project_dir, onexc=_remove_readonly)
        logger.info(
            f"Removidos {stats.files_deleted} arquivos e "
            f"{stats.directories_deleted} diretorios de {project_dir}"
        )

    except OSError as e:
        stats.files_error = f"Falha ao deletar arquivos: {e}"
        stats.files_deleted = 0
        stats.directories_deleted = 0
        logger.warning(stats.files_error)


async def _purge_project_data(project: Project) -> PurgeStats:
    """
    Remove todos os dados associados a um projeto.

    Args:
        project: Objeto Project a ser removido

    Returns:
        PurgeStats com contagem de documentos removidos
    """
    stats = PurgeStats(project_name=project.name)
    project_id = project.id

    # Remove Elements (usa Link[Project], então precisa buscar pelo $id)
    result = await Element.find({"project_id.$id": project_id}).delete()
    stats.elements = result.deleted_count if result else 0

    # Remove Controls (usa PydanticObjectId diretamente)
    result = await Control.find(Control.project_id == project_id).delete()
    stats.controls = result.deleted_count if result else 0

    # Remove Procedures
    result = await Procedure.find(Procedure.project_id == project_id).delete()
    stats.procedures = result.deleted_count if result else 0

    # Remove ClassDefinitions
    result = await ClassDefinition.find(ClassDefinition.project_id == project_id).delete()
    stats.class_definitions = result.deleted_count if result else 0

    # Remove DatabaseSchemas
    result = await DatabaseSchema.find(DatabaseSchema.project_id == project_id).delete()
    stats.schemas = result.deleted_count if result else 0

    # Remove Conversions (usa Link[Project])
    result = await Conversion.find({"project_id.$id": project_id}).delete()
    stats.conversions = result.deleted_count if result else 0

    # Remove dados do Neo4j (opcional - não falha se Neo4j não estiver disponível)
    await _purge_neo4j_data(project.name, stats)

    # Remove arquivos locais (opcional - nao falha se houver erro)
    if project.source_path:
        settings = get_settings()
        allowed_base = Path(settings.allowed_deletion_base)
        try:
            project_dir = _validate_deletion_path(project.source_path, allowed_base)
            _purge_local_files(project_dir, stats)
        except ValueError as e:
            stats.files_error = str(e)
            logger.warning(f"Path validation failed: {e}")

    # Remove o próprio projeto
    await project.delete()
    stats.projects = 1

    return stats


async def _purge_neo4j_data(project_name: str, stats: PurgeStats) -> None:
    """
    Remove dados do projeto no Neo4j.

    Esta operação é opcional - se o Neo4j não estiver disponível,
    apenas loga um aviso e continua.

    Args:
        project_name: Nome do projeto
        stats: PurgeStats para atualizar com contagem
    """
    try:
        from wxcode.graph import Neo4jConnection, Neo4jConnectionError

        async with Neo4jConnection() as conn:
            deleted = await conn.clear_project(project_name)
            stats.neo4j_nodes = deleted
            logger.info(f"Removidos {deleted} nós do Neo4j para projeto {project_name}")

    except ImportError:
        # Módulo Neo4j não disponível
        logger.debug("Módulo Neo4j não disponível, pulando limpeza")

    except Exception as e:
        # Neo4j não disponível ou erro de conexão - não é crítico
        error_msg = str(e)
        if "não disponível" in error_msg.lower() or "connection" in error_msg.lower():
            logger.warning(f"Neo4j não disponível, pulando limpeza: {error_msg}")
        else:
            logger.warning(f"Erro ao limpar Neo4j: {error_msg}")
        stats.neo4j_error = error_msg


@dataclass
class DuplicateInfo:
    """Informação sobre projetos duplicados."""
    name: str
    count: int
    ids: list[str] = field(default_factory=list)


async def check_duplicate_projects() -> list[DuplicateInfo]:
    """
    Verifica se existem projetos com nomes duplicados no banco.

    Útil para rodar antes de aplicar o índice único.

    Returns:
        Lista de DuplicateInfo para cada nome duplicado encontrado
    """
    # Agregação para encontrar nomes duplicados
    pipeline = [
        {"$group": {"_id": "$name", "count": {"$sum": 1}, "ids": {"$push": {"$toString": "$_id"}}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
    ]

    duplicates = []
    async for doc in Project.aggregate(pipeline):
        duplicates.append(DuplicateInfo(
            name=doc["_id"],
            count=doc["count"],
            ids=doc["ids"],
        ))

    return duplicates


async def get_project_by_name(name: str) -> Optional[Project]:
    """
    Busca um projeto pelo nome.

    Args:
        name: Nome do projeto

    Returns:
        Project se encontrado, None caso contrário
    """
    return await Project.find_one(Project.name == name)
