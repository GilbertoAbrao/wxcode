"""
Testes para WorkspaceManager.

Usa tmp_path e monkeypatch para isolamento completo do filesystem real.
"""

import json
import re
import pytest
from pathlib import Path

from wxcode.services.workspace_manager import WorkspaceManager
from wxcode.models.workspace import WorkspaceMetadata, PRODUCT_TYPES


@pytest.fixture
def mock_workspaces_base(tmp_path, monkeypatch):
    """Configura WORKSPACES_BASE para diretorio temporario."""
    workspaces_base = tmp_path / "workspaces"
    monkeypatch.setattr(WorkspaceManager, "WORKSPACES_BASE", workspaces_base)
    return workspaces_base


class TestEnsureBaseDirectory:
    """Testes para ensure_base_directory()."""

    def test_ensure_base_directory_creates_path(self, mock_workspaces_base):
        """Deve criar o diretorio base se nao existir."""
        assert not mock_workspaces_base.exists()

        result = WorkspaceManager.ensure_base_directory()

        assert result == mock_workspaces_base
        assert mock_workspaces_base.exists()
        assert mock_workspaces_base.is_dir()


class TestCreateWorkspace:
    """Testes para create_workspace()."""

    def test_create_workspace_creates_directory(self, mock_workspaces_base):
        """Deve criar diretorio do workspace."""
        path, metadata = WorkspaceManager.create_workspace(
            "Test Project",
            "/path/to/source.wwp"
        )

        assert path.exists()
        assert path.is_dir()
        assert path.parent == mock_workspaces_base

    def test_create_workspace_creates_metadata_file(self, mock_workspaces_base):
        """Deve criar arquivo .workspace.json dentro do workspace."""
        path, metadata = WorkspaceManager.create_workspace(
            "Test Project",
            "/path/to/source.wwp"
        )

        meta_file = path / ".workspace.json"
        assert meta_file.exists()

    def test_create_workspace_sanitizes_name(self, mock_workspaces_base):
        """Deve sanitizar nome do projeto no nome do diretorio."""
        path, metadata = WorkspaceManager.create_workspace(
            "My Project/Test",
            "/path/to/source.wwp"
        )

        # Nome deve ser sanitizado: lowercase, caracteres inseguros -> _
        dir_name = path.name
        # Format: {sanitized_name}_{8hexchars}
        match = re.match(r'^([a-z0-9_]+)_([a-f0-9]{8})$', dir_name)
        assert match is not None

        sanitized_part = match.group(1)
        assert sanitized_part == "my_project_test"


class TestWorkspaceMetadataContent:
    """Testes para conteudo do metadata."""

    def test_workspace_metadata_content(self, mock_workspaces_base):
        """Deve ter todos os campos obrigatorios no metadata."""
        path, metadata = WorkspaceManager.create_workspace(
            "Test Project",
            "/original/path/project.wwp"
        )

        meta_file = path / ".workspace.json"
        content = json.loads(meta_file.read_text())

        assert "workspace_id" in content
        assert "project_name" in content
        assert "created_at" in content
        assert "imported_from" in content

        # workspace_id deve ser 8 hex chars
        assert re.match(r'^[a-f0-9]{8}$', content["workspace_id"])

        # project_name deve ser o original (nao sanitizado)
        assert content["project_name"] == "Test Project"

        # imported_from deve ser o path original
        assert content["imported_from"] == "/original/path/project.wwp"


class TestReadWorkspaceMetadata:
    """Testes para read_workspace_metadata()."""

    def test_read_workspace_metadata_returns_none_for_missing(self, tmp_path):
        """Deve retornar None para path inexistente."""
        result = WorkspaceManager.read_workspace_metadata(tmp_path / "nonexistent")
        assert result is None

    def test_read_workspace_metadata_returns_none_for_missing_file(self, tmp_path):
        """Deve retornar None para diretorio sem .workspace.json."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()

        result = WorkspaceManager.read_workspace_metadata(workspace_dir)
        assert result is None

    def test_read_workspace_metadata_returns_valid_metadata(self, mock_workspaces_base):
        """Deve retornar metadata valido para workspace existente."""
        path, created_metadata = WorkspaceManager.create_workspace(
            "Test Project",
            "/path/to/source.wwp"
        )

        read_metadata = WorkspaceManager.read_workspace_metadata(path)

        assert read_metadata is not None
        assert read_metadata.workspace_id == created_metadata.workspace_id
        assert read_metadata.project_name == created_metadata.project_name


class TestListWorkspaces:
    """Testes para list_workspaces()."""

    def test_list_workspaces_finds_valid(self, mock_workspaces_base):
        """Deve encontrar todos os workspaces validos."""
        # Cria 2 workspaces
        path1, meta1 = WorkspaceManager.create_workspace("Project 1", "/p1.wwp")
        path2, meta2 = WorkspaceManager.create_workspace("Project 2", "/p2.wwp")

        result = WorkspaceManager.list_workspaces()

        assert len(result) == 2
        paths = [p for p, m in result]
        assert path1 in paths
        assert path2 in paths

    def test_list_workspaces_skips_invalid(self, mock_workspaces_base):
        """Deve ignorar diretorios sem .workspace.json valido."""
        # Cria 1 workspace valido
        path1, meta1 = WorkspaceManager.create_workspace("Project 1", "/p1.wwp")

        # Cria 1 diretorio invalido (sem .workspace.json)
        invalid_dir = mock_workspaces_base / "invalid_workspace"
        invalid_dir.mkdir()

        result = WorkspaceManager.list_workspaces()

        assert len(result) == 1
        paths = [p for p, m in result]
        assert path1 in paths
        assert invalid_dir not in paths

    def test_list_workspaces_returns_empty_for_no_base(self, mock_workspaces_base):
        """Deve retornar lista vazia se base nao existir."""
        # Base nao existe ainda
        assert not mock_workspaces_base.exists()

        result = WorkspaceManager.list_workspaces()

        assert result == []


class TestEnsureProductDirectory:
    """Testes para ensure_product_directory()."""

    def test_ensure_product_directory_creates(self, mock_workspaces_base):
        """Deve criar subdiretorio de produto."""
        ws_path, _ = WorkspaceManager.create_workspace("Test", "/test.wwp")

        result = WorkspaceManager.ensure_product_directory(ws_path, "conversion")

        assert result == ws_path / "conversion"
        assert result.exists()
        assert result.is_dir()

    def test_ensure_product_directory_all_types(self, mock_workspaces_base):
        """Deve aceitar todos os tipos de produto."""
        ws_path, _ = WorkspaceManager.create_workspace("Test", "/test.wwp")

        for product_type in PRODUCT_TYPES:
            result = WorkspaceManager.ensure_product_directory(ws_path, product_type)
            assert result.exists()

    def test_ensure_product_directory_rejects_invalid(self, mock_workspaces_base):
        """Deve rejeitar tipo de produto invalido."""
        ws_path, _ = WorkspaceManager.create_workspace("Test", "/test.wwp")

        with pytest.raises(ValueError) as exc_info:
            WorkspaceManager.ensure_product_directory(ws_path, "invalid_type")

        assert "invalid_type" in str(exc_info.value)
        assert "invalido" in str(exc_info.value).lower()
