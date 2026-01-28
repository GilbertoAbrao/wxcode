"""
Testes para Neo4jSyncService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from wxcode.graph.neo4j_sync import Neo4jSyncService, SyncResult


class TestSyncResult:
    """Testes para SyncResult."""

    def test_success_when_no_errors(self):
        """Testa que success é True quando não há erros."""
        result = SyncResult(project_name="Test")
        assert result.success is True

    def test_success_when_has_errors(self):
        """Testa que success é False quando há erros."""
        result = SyncResult(project_name="Test", errors=["Error 1"])
        assert result.success is False

    def test_str_format(self):
        """Testa formato de string."""
        result = SyncResult(
            project_name="Test",
            nodes_created=10,
            relationships_created=5,
        )
        assert "Test" in str(result)
        assert "10" in str(result)
        assert "5" in str(result)


class TestNeo4jSyncService:
    """Testes para Neo4jSyncService."""

    @pytest.fixture
    def mock_connection(self):
        """Mock da conexão Neo4j."""
        conn = AsyncMock()
        conn.batch_create.return_value = 0
        conn.execute.return_value = [{"count": 0}]
        conn.clear_project.return_value = 0
        conn.create_indexes.return_value = None
        conn.get_stats.return_value = {}
        return conn

    @pytest.fixture
    def sync_service(self, mock_connection):
        """Serviço de sincronização com mock."""
        return Neo4jSyncService(mock_connection)

    @pytest.mark.asyncio
    async def test_sync_project_not_found(self, sync_service):
        """Testa sync de projeto não encontrado."""
        with patch("wxcode.graph.neo4j_sync.Project") as mock_project:
            # Project.get is async, so use AsyncMock
            mock_project.get = AsyncMock(return_value=None)

            with pytest.raises(ValueError) as exc_info:
                await sync_service.sync_project(ObjectId())

            assert "não encontrado" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sync_tables_empty(self, sync_service):
        """Testa sincronização de tabelas quando não há schema."""
        project_id = ObjectId()

        with patch("wxcode.graph.neo4j_sync.DatabaseSchema") as mock_schema:
            mock_schema.find_one = AsyncMock(return_value=None)

            count = await sync_service._sync_tables(project_id, "TestProject")

            assert count == 0

    @pytest.mark.asyncio
    async def test_sync_tables_with_data(self, sync_service, mock_connection):
        """Testa sincronização de tabelas com dados."""
        project_id = ObjectId()

        mock_schema = MagicMock()
        mock_schema.tables = [
            MagicMock(
                name="CLIENTE",
                physical_name="CLIENTE",
                connection_name="CNX_BASE",
                columns=[MagicMock()],
            ),
            MagicMock(
                name="PEDIDO",
                physical_name="PEDIDO",
                connection_name="CNX_BASE",
                columns=[MagicMock(), MagicMock()],
            ),
        ]

        with patch("wxcode.graph.neo4j_sync.DatabaseSchema") as mock_db_schema:
            mock_db_schema.find_one = AsyncMock(return_value=mock_schema)

            count = await sync_service._sync_tables(project_id, "TestProject")

            assert count == 2
            mock_connection.batch_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_classes_empty(self, sync_service):
        """Testa sincronização de classes sem dados."""
        project_id = ObjectId()

        with patch("wxcode.graph.neo4j_sync.ClassDefinition") as mock_class:
            mock_find = AsyncMock()
            mock_find.to_list = AsyncMock(return_value=[])
            mock_class.find.return_value = mock_find

            count = await sync_service._sync_classes(project_id, "TestProject")

            assert count == 0

    @pytest.mark.asyncio
    async def test_sync_classes_with_data(self, sync_service, mock_connection):
        """Testa sincronização de classes com dados."""
        project_id = ObjectId()

        mock_classes = [
            MagicMock(
                id=ObjectId(),
                name="classCliente",
                inherits_from="classBase",
                is_abstract=False,
                members=[MagicMock()],
                methods=[MagicMock(), MagicMock()],
            ),
        ]

        with patch("wxcode.graph.neo4j_sync.ClassDefinition") as mock_class:
            mock_find = AsyncMock()
            mock_find.to_list = AsyncMock(return_value=mock_classes)
            mock_class.find.return_value = mock_find

            count = await sync_service._sync_classes(project_id, "TestProject")

            assert count == 1
            mock_connection.batch_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_dry_run_returns_counts(self, sync_service):
        """Testa que dry_run retorna contagens sem modificar."""
        project_id = ObjectId()

        mock_schema = MagicMock()
        mock_schema.tables = [MagicMock(), MagicMock()]

        with patch("wxcode.graph.neo4j_sync.Project") as mock_project, \
             patch("wxcode.graph.neo4j_sync.DatabaseSchema") as mock_db_schema, \
             patch("wxcode.graph.neo4j_sync.ClassDefinition") as mock_class, \
             patch("wxcode.graph.neo4j_sync.Procedure") as mock_proc, \
             patch("wxcode.graph.neo4j_sync.Element") as mock_elem:

            mock_project.get = AsyncMock(return_value=MagicMock(name="TestProject"))
            mock_db_schema.find_one = AsyncMock(return_value=mock_schema)

            mock_class_find = AsyncMock()
            mock_class_find.count = AsyncMock(return_value=5)
            mock_class.find.return_value = mock_class_find

            mock_proc_find = AsyncMock()
            mock_proc_find.count = AsyncMock(return_value=10)
            mock_proc.find.return_value = mock_proc_find

            mock_elem_find = AsyncMock()
            mock_elem_find.to_list = AsyncMock(return_value=[])
            mock_elem.find.return_value = mock_elem_find

            result = await sync_service.dry_run(project_id)

            assert result.tables_count == 2
            assert result.classes_count == 5
            assert result.procedures_count == 10
