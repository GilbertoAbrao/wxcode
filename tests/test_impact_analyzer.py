"""
Testes para ImpactAnalyzer.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from wxcode.graph.impact_analyzer import (
    ImpactAnalyzer,
    ImpactResult,
    AffectedNode,
    PathResult,
    PathNode,
    HubResult,
    HubNode,
    DeadCodeResult,
)


class TestImpactResult:
    """Testes para ImpactResult."""

    def test_total_affected(self):
        """Testa contagem de afetados."""
        result = ImpactResult(
            source_name="test",
            source_type="Table",
            affected=[
                AffectedNode(name="a", node_type="Class", depth=1),
                AffectedNode(name="b", node_type="Procedure", depth=2),
            ],
        )
        assert result.total_affected == 2

    def test_by_depth(self):
        """Testa agrupamento por profundidade."""
        result = ImpactResult(
            source_name="test",
            source_type="Table",
            affected=[
                AffectedNode(name="a", node_type="Class", depth=1),
                AffectedNode(name="b", node_type="Procedure", depth=1),
                AffectedNode(name="c", node_type="Page", depth=2),
            ],
        )

        by_depth = result.by_depth()
        assert len(by_depth[1]) == 2
        assert len(by_depth[2]) == 1

    def test_by_type(self):
        """Testa agrupamento por tipo."""
        result = ImpactResult(
            source_name="test",
            source_type="Table",
            affected=[
                AffectedNode(name="a", node_type="Class", depth=1),
                AffectedNode(name="b", node_type="Class", depth=2),
                AffectedNode(name="c", node_type="Procedure", depth=1),
            ],
        )

        by_type = result.by_type()
        assert len(by_type["Class"]) == 2
        assert len(by_type["Procedure"]) == 1


class TestPathResult:
    """Testes para PathResult."""

    def test_shortest_length_empty(self):
        """Testa caminho mais curto sem caminhos."""
        result = PathResult(source="a", target="b")
        assert result.shortest_length is None

    def test_shortest_length(self):
        """Testa caminho mais curto."""
        result = PathResult(
            source="a",
            target="b",
            paths=[
                [PathNode("a", "Page"), PathNode("x", "Procedure"), PathNode("b", "Table")],
                [PathNode("a", "Page"), PathNode("b", "Table")],
            ],
        )
        assert result.shortest_length == 2


class TestHubNode:
    """Testes para HubNode."""

    def test_total_connections(self):
        """Testa total de conexões."""
        hub = HubNode(name="test", node_type="Procedure", incoming=10, outgoing=5)
        assert hub.total_connections == 15


class TestDeadCodeResult:
    """Testes para DeadCodeResult."""

    def test_total(self):
        """Testa total de código morto."""
        result = DeadCodeResult(
            procedures=["proc1", "proc2"],
            classes=["class1"],
        )
        assert result.total == 3


class TestImpactAnalyzer:
    """Testes para ImpactAnalyzer."""

    @pytest.fixture
    def mock_connection(self):
        """Mock da conexão Neo4j."""
        return AsyncMock()

    @pytest.fixture
    def analyzer(self, mock_connection):
        """Analisador com mock."""
        return ImpactAnalyzer(mock_connection)

    @pytest.mark.asyncio
    async def test_get_impact_node_not_found(self, analyzer, mock_connection):
        """Testa impacto de nó não encontrado."""
        mock_connection.execute.return_value = [{"source_name": None}]

        result = await analyzer.get_impact("INEXISTENTE")

        assert result.error is not None
        assert "não encontrado" in result.error

    @pytest.mark.asyncio
    async def test_get_impact_success(self, analyzer, mock_connection):
        """Testa análise de impacto bem sucedida."""
        mock_connection.execute.return_value = [
            {
                "source_name": "CLIENTE",
                "source_type": "Table",
                "affected_nodes": [
                    {"name": "classCliente", "type": "Class", "depth": 1},
                    {"name": "proc:ValidaCPF", "type": "Procedure", "depth": 2},
                ],
            }
        ]

        result = await analyzer.get_impact("TABLE:CLIENTE")

        assert result.source_name == "CLIENTE"
        assert result.source_type == "Table"
        assert result.total_affected == 2
        assert result.affected[0].depth == 1  # Ordenado por depth

    @pytest.mark.asyncio
    async def test_get_impact_parses_node_id(self, analyzer, mock_connection):
        """Testa parsing do node_id."""
        mock_connection.execute.return_value = [
            {"source_name": "CLIENTE", "source_type": "Table", "affected_nodes": []}
        ]

        await analyzer.get_impact("TABLE:CLIENTE")

        call_args = mock_connection.execute.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "TABLE" in query
        assert params["name"] == "CLIENTE"

    @pytest.mark.asyncio
    async def test_get_path_no_path(self, analyzer, mock_connection):
        """Testa quando não há caminho."""
        mock_connection.execute.return_value = []

        result = await analyzer.get_path("A", "B")

        assert result.error is not None
        assert "Nenhum caminho" in result.error

    @pytest.mark.asyncio
    async def test_find_hubs(self, analyzer, mock_connection):
        """Testa busca de hubs."""
        mock_connection.execute.return_value = [
            {"name": "RESTSend", "type": "Procedure", "incoming": 45, "outgoing": 3},
            {"name": "CLIENTE", "type": "Table", "incoming": 0, "outgoing": 28},
        ]

        result = await analyzer.find_hubs(min_connections=10)

        assert len(result.hubs) == 2
        assert result.hubs[0].name == "RESTSend"
        assert result.hubs[0].total_connections == 48

    @pytest.mark.asyncio
    async def test_find_hubs_empty(self, analyzer, mock_connection):
        """Testa quando não há hubs."""
        mock_connection.execute.return_value = []

        result = await analyzer.find_hubs(min_connections=100)

        assert len(result.hubs) == 0
        assert result.error is None

    @pytest.mark.asyncio
    async def test_find_dead_code(self, analyzer, mock_connection):
        """Testa busca de código morto."""
        # Primeiro call para procedures, segundo para classes
        mock_connection.execute.side_effect = [
            [{"name": "OrphanProc1"}, {"name": "OrphanProc2"}],
            [{"name": "UnusedClass"}],
        ]

        result = await analyzer.find_dead_code()

        assert len(result.procedures) == 2
        assert len(result.classes) == 1
        assert result.total == 3

    @pytest.mark.asyncio
    async def test_find_dead_code_excludes_entry_points(self, analyzer, mock_connection):
        """Testa que entry points são excluídos."""
        mock_connection.execute.return_value = []

        await analyzer.find_dead_code(
            entry_point_prefixes=["API", "Task", "PAGE_"]
        )

        call_args = mock_connection.execute.call_args_list[0]
        query = call_args[0][0]

        assert "NOT n.name STARTS WITH 'API'" in query
        assert "NOT n.name STARTS WITH 'Task'" in query
        assert "NOT n.name STARTS WITH 'PAGE_'" in query

    @pytest.mark.asyncio
    async def test_find_cycles(self, analyzer, mock_connection):
        """Testa busca de ciclos."""
        mock_connection.execute.return_value = [
            {"cycle": ["A", "B", "C", "A"]},
            {"cycle": ["X", "Y", "X"]},  # Ciclo diferente
        ]

        cycles = await analyzer.find_cycles()

        # Dois ciclos distintos
        assert len(cycles) == 2

    @pytest.mark.asyncio
    async def test_error_handling(self, analyzer, mock_connection):
        """Testa tratamento de erros."""
        mock_connection.execute.side_effect = Exception("Connection lost")

        result = await analyzer.get_impact("test")

        assert result.error is not None
        assert "Connection lost" in result.error
