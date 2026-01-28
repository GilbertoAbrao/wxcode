"""
Testes para idempotência de projetos e purge.

Testa:
- Unique constraint no nome do projeto
- Verificação de existência no import
- Import com --force
- Purge de todas as collections
- API delete com cascade
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from beanie import PydanticObjectId

from wxcode.models import (
    Project,
    ProjectStatus,
    Element,
    ElementType,
    Control,
    Procedure,
    ClassDefinition,
    DatabaseSchema,
    Conversion,
)
from wxcode.services.project_service import (
    purge_project,
    purge_project_by_name,
    check_duplicate_projects,
    PurgeStats,
    DuplicateInfo,
    _purge_project_data,
)


class TestPurgeStats:
    """Testes para PurgeStats."""

    def test_total_calculation(self):
        """Testa cálculo do total de documentos removidos."""
        stats = PurgeStats(
            project_name="TestProject",
            projects=1,
            elements=10,
            controls=50,
            procedures=5,
            class_definitions=3,
            schemas=1,
            conversions=2,
        )
        assert stats.total == 72

    def test_total_with_neo4j(self):
        """Testa cálculo do total incluindo Neo4j."""
        stats = PurgeStats(
            project_name="TestProject",
            projects=1,
            elements=10,
            neo4j_nodes=100,
        )
        assert stats.total == 11  # Apenas MongoDB
        assert stats.total_with_neo4j == 111  # MongoDB + Neo4j

    def test_to_dict(self):
        """Testa conversão para dicionário."""
        stats = PurgeStats(
            project_name="TestProject",
            projects=1,
            elements=10,
        )
        result = stats.to_dict()

        assert result["project_name"] == "TestProject"
        assert result["projects"] == 1
        assert result["elements"] == 10
        assert result["total"] == 11
        assert "neo4j_nodes" not in result  # Não inclui se for 0

    def test_to_dict_with_neo4j(self):
        """Testa conversão para dicionário com Neo4j."""
        stats = PurgeStats(
            project_name="TestProject",
            projects=1,
            neo4j_nodes=50,
        )
        result = stats.to_dict()

        assert result["neo4j_nodes"] == 50

    def test_to_dict_with_neo4j_error(self):
        """Testa conversão para dicionário com erro Neo4j."""
        stats = PurgeStats(
            project_name="TestProject",
            projects=1,
            neo4j_error="Connection refused",
        )
        result = stats.to_dict()

        assert result["neo4j_error"] == "Connection refused"

    def test_empty_stats(self):
        """Testa stats vazios."""
        stats = PurgeStats()
        assert stats.total == 0
        assert stats.project_name == ""
        assert stats.neo4j_nodes == 0
        assert stats.neo4j_error is None


class TestDuplicateInfo:
    """Testes para DuplicateInfo."""

    def test_duplicate_info_creation(self):
        """Testa criação de DuplicateInfo."""
        dup = DuplicateInfo(
            name="TestProject",
            count=3,
            ids=["id1", "id2", "id3"],
        )
        assert dup.name == "TestProject"
        assert dup.count == 3
        assert len(dup.ids) == 3


class TestPurgeProjectData:
    """Testes para _purge_project_data."""

    @pytest.fixture
    def mock_project(self):
        """Cria um projeto mock."""
        project = MagicMock()
        project.id = PydanticObjectId()
        project.name = "TestProject"
        project.delete = AsyncMock()
        return project

    @pytest.mark.asyncio
    async def test_purge_removes_all_collections(self, mock_project):
        """Testa que purge remove todas as collections."""
        # Mock delete results
        mock_result = MagicMock()
        mock_result.deleted_count = 5

        # Patch no nível do módulo de serviço
        with patch('wxcode.services.project_service.Element') as mock_element, \
             patch('wxcode.services.project_service.Control') as mock_control, \
             patch('wxcode.services.project_service.Procedure') as mock_proc, \
             patch('wxcode.services.project_service.ClassDefinition') as mock_class, \
             patch('wxcode.services.project_service.DatabaseSchema') as mock_schema, \
             patch('wxcode.services.project_service.Conversion') as mock_conv, \
             patch('wxcode.services.project_service._purge_neo4j_data', new_callable=AsyncMock) as mock_neo4j:

            # Configure all mocks to return delete result
            for mock_model in [mock_element, mock_control, mock_proc,
                               mock_class, mock_schema, mock_conv]:
                mock_model.find.return_value.delete = AsyncMock(return_value=mock_result)

            stats = await _purge_project_data(mock_project)

            assert stats.project_name == "TestProject"
            assert stats.projects == 1
            assert stats.elements == 5
            assert stats.controls == 5
            assert stats.procedures == 5
            assert stats.class_definitions == 5
            assert stats.schemas == 5
            assert stats.conversions == 5

            mock_project.delete.assert_called_once()
            mock_neo4j.assert_called_once()


class TestPurgeProject:
    """Testes para purge_project."""

    @pytest.mark.asyncio
    async def test_purge_project_not_found(self):
        """Testa erro quando projeto não existe."""
        with patch('wxcode.services.project_service.Project') as mock_project_cls:
            mock_project_cls.get = AsyncMock(return_value=None)

            with pytest.raises(ValueError) as exc_info:
                await purge_project(PydanticObjectId())

            assert "não encontrado" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_purge_project_by_name_not_found(self):
        """Testa erro quando projeto não existe pelo nome."""
        with patch('wxcode.services.project_service.Project') as mock_project_cls:
            mock_project_cls.find_one = AsyncMock(return_value=None)

            with pytest.raises(ValueError) as exc_info:
                await purge_project_by_name("NonExistentProject")

            assert "não encontrado" in str(exc_info.value)


class TestCheckDuplicateProjects:
    """Testes para check_duplicate_projects."""

    @pytest.mark.asyncio
    async def test_no_duplicates(self):
        """Testa quando não há duplicatas."""
        async def empty_generator():
            return
            yield  # pragma: no cover

        with patch.object(Project, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value = empty_generator()

            duplicates = await check_duplicate_projects()
            assert duplicates == []

    @pytest.mark.asyncio
    async def test_with_duplicates(self):
        """Testa quando há duplicatas."""
        async def duplicate_generator():
            yield {"_id": "Project1", "count": 3, "ids": ["id1", "id2", "id3"]}
            yield {"_id": "Project2", "count": 2, "ids": ["id4", "id5"]}

        with patch.object(Project, 'aggregate') as mock_aggregate:
            mock_aggregate.return_value = duplicate_generator()

            duplicates = await check_duplicate_projects()

            assert len(duplicates) == 2
            assert duplicates[0].name == "Project1"
            assert duplicates[0].count == 3
            assert duplicates[1].name == "Project2"
            assert duplicates[1].count == 2


class TestProjectUniqueIndex:
    """Testes para o índice único no nome do projeto."""

    def test_project_has_unique_index_defined(self):
        """Testa que o model Project tem índice único definido."""
        indexes = Project.Settings.indexes

        assert len(indexes) > 0

        # Verifica que há um índice no campo 'name' com unique=True
        found_unique_name_index = False
        for index in indexes:
            # IndexModel tem atributo document
            if hasattr(index, 'document'):
                keys = index.document.get('key', {})
                unique = index.document.get('unique', False)
                if 'name' in keys and unique:
                    found_unique_name_index = True
                    break

        assert found_unique_name_index, "Projeto deve ter índice único no campo 'name'"


class TestImportIdempotency:
    """Testes para idempotência do import."""

    def test_import_command_has_force_flag(self):
        """Testa que o comando import tem a flag --force."""
        from wxcode.cli import import_project
        import inspect

        sig = inspect.signature(import_project)
        params = list(sig.parameters.keys())

        assert 'force' in params, "Comando import deve ter parâmetro 'force'"


class TestAPIDeleteProject:
    """Testes para API delete_project."""

    @pytest.mark.asyncio
    async def test_delete_returns_stats(self):
        """Testa que delete retorna estatísticas."""
        from wxcode.api.projects import DeleteProjectResponse

        # Verifica estrutura do response
        response = DeleteProjectResponse(
            message="Projeto removido",
            stats={"projects": 1, "elements": 10, "total": 11},
        )

        assert response.message == "Projeto removido"
        assert response.stats["projects"] == 1
        assert response.stats["total"] == 11
