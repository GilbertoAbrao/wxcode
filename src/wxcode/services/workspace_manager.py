"""
Gerenciador de workspaces.

Responsavel por criar e gerenciar diretorios de workspace isolados
em ~/.wxcode/workspaces/.
"""

import logging
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from wxcode.models.workspace import WorkspaceMetadata, PRODUCT_TYPES


logger = logging.getLogger(__name__)


class WorkspaceManager:
    """
    Gerencia operacoes de diretorio de workspace.

    Todos os metodos sao classmethod ou staticmethod pois nao ha
    estado de instancia - apenas operacoes no filesystem.
    """

    # Diretorio base para todos os workspaces
    WORKSPACES_BASE: Path = Path.home() / ".wxcode" / "workspaces"

    @classmethod
    def ensure_base_directory(cls) -> Path:
        """
        Cria o diretorio base ~/.wxcode/workspaces/ se nao existir.

        Returns:
            Path do diretorio base
        """
        try:
            cls.WORKSPACES_BASE.mkdir(parents=True, exist_ok=True)
            return cls.WORKSPACES_BASE
        except OSError as e:
            logger.error(f"Falha ao criar diretorio base: {e}")
            raise

    @classmethod
    def create_workspace(
        cls,
        project_name: str,
        imported_from: str
    ) -> tuple[Path, WorkspaceMetadata]:
        """
        Cria um novo diretorio de workspace com metadados.

        Args:
            project_name: Nome original do projeto
            imported_from: Caminho do arquivo .wwp de origem

        Returns:
            Tupla de (workspace_path, metadata)
        """
        cls.ensure_base_directory()

        workspace_id = secrets.token_hex(4)
        sanitized_name = cls._sanitize_name(project_name)
        dir_name = f"{sanitized_name}_{workspace_id}"
        workspace_path = cls.WORKSPACES_BASE / dir_name

        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Falha ao criar workspace: {e}")
            raise

        metadata = WorkspaceMetadata(
            workspace_id=workspace_id,
            project_name=project_name,
            created_at=datetime.now(timezone.utc),
            imported_from=imported_from,
        )

        cls._write_metadata(workspace_path, metadata)

        logger.info(f"Workspace criado: {workspace_path}")
        return workspace_path, metadata

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """
        Sanitiza nome do projeto para uso no filesystem.

        Converte para lowercase, substitui caracteres inseguros por _,
        e limita a 50 caracteres.

        Args:
            name: Nome original do projeto

        Returns:
            Nome sanitizado
        """
        return re.sub(r'[^a-z0-9_]', '_', name.lower())[:50]

    @staticmethod
    def _write_metadata(workspace_path: Path, metadata: WorkspaceMetadata) -> None:
        """
        Escreve arquivo .workspace.json no diretorio do workspace.

        Args:
            workspace_path: Path do diretorio do workspace
            metadata: Metadados a serem gravados
        """
        meta_file = workspace_path / ".workspace.json"
        meta_file.write_text(metadata.model_dump_json(indent=2))

    @classmethod
    def read_workspace_metadata(cls, workspace_path: Path) -> WorkspaceMetadata | None:
        """
        Le metadados de um workspace existente.

        Args:
            workspace_path: Path do diretorio do workspace

        Returns:
            WorkspaceMetadata se .workspace.json existir, None caso contrario
        """
        meta_file = workspace_path / ".workspace.json"
        if not meta_file.exists():
            return None

        try:
            return WorkspaceMetadata.model_validate_json(meta_file.read_text())
        except Exception as e:
            logger.warning(f"Falha ao ler metadata de {workspace_path}: {e}")
            return None

    @classmethod
    def list_workspaces(cls) -> list[tuple[Path, WorkspaceMetadata]]:
        """
        Lista todos os workspaces validos.

        Percorre o diretorio base e retorna apenas workspaces
        que tem .workspace.json valido.

        Returns:
            Lista de tuplas (path, metadata)
        """
        if not cls.WORKSPACES_BASE.exists():
            return []

        workspaces = []
        for workspace_dir in cls.WORKSPACES_BASE.iterdir():
            if workspace_dir.is_dir():
                metadata = cls.read_workspace_metadata(workspace_dir)
                if metadata:
                    workspaces.append((workspace_dir, metadata))

        return workspaces

    @classmethod
    def ensure_product_directory(cls, workspace_path: Path, product_type: str) -> Path:
        """
        Cria subdiretorio de produto se nao existir.

        Args:
            workspace_path: Path do diretorio do workspace
            product_type: Tipo de produto (conversion, api, mcp, agents)

        Returns:
            Path do diretorio de produto

        Raises:
            ValueError: Se product_type nao for valido
        """
        if product_type not in PRODUCT_TYPES:
            raise ValueError(
                f"Tipo de produto invalido: '{product_type}'. "
                f"Valores validos: {PRODUCT_TYPES}"
            )

        product_dir = workspace_path / product_type
        try:
            product_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Falha ao criar diretorio de produto: {e}")
            raise

        return product_dir

    @classmethod
    def create_output_project_workspace(
        cls,
        project_name: str,
        stack_id: str,
    ) -> Path:
        """
        Cria workspace para um OutputProject.

        OutputProjects sao armazenados em:
        ~/.wxcode/workspaces/output-projects/{project_name}_{id}/

        Args:
            project_name: Nome do output project
            stack_id: ID da stack alvo

        Returns:
            Path do diretorio do workspace
        """
        cls.ensure_base_directory()

        # Output projects vao em subdiretorio separado
        output_projects_base = cls.WORKSPACES_BASE / "output-projects"
        try:
            output_projects_base.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Falha ao criar diretorio base de output-projects: {e}")
            raise

        workspace_id = secrets.token_hex(4)
        sanitized_name = cls._sanitize_name(project_name)
        dir_name = f"{sanitized_name}_{workspace_id}"
        workspace_path = output_projects_base / dir_name

        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Falha ao criar workspace de output project: {e}")
            raise

        # Cria arquivo de metadados simplificado
        meta_file = workspace_path / ".output-project.json"
        import json
        meta_data = {
            "workspace_id": workspace_id,
            "project_name": project_name,
            "stack_id": stack_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        meta_file.write_text(json.dumps(meta_data, indent=2))

        logger.info(f"Output project workspace criado: {workspace_path}")
        return workspace_path

    @classmethod
    def create_kb_workspace(
        cls,
        project_name: str,
        imported_from: str,
    ) -> Path:
        """
        Cria workspace para uma Knowledge Base.

        Knowledge Bases sao armazenadas em:
        ~/.wxcode/workspaces/knowledge-bases/{project_name}_{id}/

        Args:
            project_name: Nome do projeto/KB
            imported_from: Caminho do arquivo .wwp de origem

        Returns:
            Path do diretorio do workspace
        """
        cls.ensure_base_directory()

        # Knowledge bases vao em subdiretorio separado
        kb_base = cls.WORKSPACES_BASE / "knowledge-bases"
        try:
            kb_base.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Falha ao criar diretorio base de knowledge-bases: {e}")
            raise

        workspace_id = secrets.token_hex(4)
        sanitized_name = cls._sanitize_name(project_name)
        dir_name = f"{sanitized_name}_{workspace_id}"
        workspace_path = kb_base / dir_name

        try:
            workspace_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Falha ao criar workspace de knowledge base: {e}")
            raise

        # Cria arquivo de metadados
        meta_file = workspace_path / ".knowledge-base.json"
        import json
        meta_data = {
            "workspace_id": workspace_id,
            "project_name": project_name,
            "imported_from": imported_from,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        meta_file.write_text(json.dumps(meta_data, indent=2))

        logger.info(f"Knowledge base workspace criado: {workspace_path}")
        return workspace_path
