"""
Testes para o módulo de análise de dependências.

Testa:
- Models (NodeType, EdgeType, GraphNode, etc.)
- CycleDetector
- TopologicalSorter
- GraphBuilder (com mocks do MongoDB)
"""

import pytest
import networkx as nx

from wxcode.analyzer.models import (
    NodeType,
    EdgeType,
    GraphNode,
    GraphEdge,
    CycleInfo,
    LayerStats,
    AnalysisResult,
)
from wxcode.analyzer.cycle_detector import CycleDetector
from wxcode.analyzer.topological_sorter import TopologicalSorter
from wxcode.models.element import ElementLayer


class TestNodeType:
    """Testes para NodeType enum."""

    def test_node_types_exist(self):
        """Verifica que todos os tipos de nó existem."""
        assert NodeType.TABLE.value == "table"
        assert NodeType.CLASS.value == "class"
        assert NodeType.PROCEDURE.value == "procedure"
        assert NodeType.PAGE.value == "page"
        assert NodeType.WINDOW.value == "window"
        assert NodeType.QUERY.value == "query"


class TestEdgeType:
    """Testes para EdgeType enum."""

    def test_edge_types_exist(self):
        """Verifica que todos os tipos de aresta existem."""
        assert EdgeType.INHERITS.value == "inherits"
        assert EdgeType.USES_CLASS.value == "uses_class"
        assert EdgeType.CALLS_PROCEDURE.value == "calls_proc"
        assert EdgeType.USES_TABLE.value == "uses_table"
        assert EdgeType.USES_QUERY.value == "uses_query"


class TestGraphNode:
    """Testes para GraphNode model."""

    def test_create_node(self):
        """Testa criação de nó."""
        node = GraphNode(
            id="table:CLIENTE",
            name="CLIENTE",
            node_type=NodeType.TABLE,
            layer=ElementLayer.SCHEMA
        )
        assert node.id == "table:CLIENTE"
        assert node.name == "CLIENTE"
        assert node.node_type == NodeType.TABLE
        assert node.layer == ElementLayer.SCHEMA
        assert node.mongo_id is None
        assert node.collection is None

    def test_node_str(self):
        """Testa representação string do nó."""
        node = GraphNode(
            id="proc:ValidaCPF",
            name="ValidaCPF",
            node_type=NodeType.PROCEDURE,
            layer=ElementLayer.BUSINESS
        )
        assert str(node) == "procedure:ValidaCPF"


class TestGraphEdge:
    """Testes para GraphEdge model."""

    def test_create_edge(self):
        """Testa criação de aresta."""
        edge = GraphEdge(
            source="class:Usuario",
            target="class:Pessoa",
            edge_type=EdgeType.INHERITS
        )
        assert edge.source == "class:Usuario"
        assert edge.target == "class:Pessoa"
        assert edge.edge_type == EdgeType.INHERITS
        assert edge.weight == 1

    def test_edge_str(self):
        """Testa representação string da aresta."""
        edge = GraphEdge(
            source="page:Login",
            target="proc:Autenticar",
            edge_type=EdgeType.CALLS_PROCEDURE
        )
        assert str(edge) == "page:Login --[calls_proc]--> proc:Autenticar"


class TestCycleInfo:
    """Testes para CycleInfo model."""

    def test_create_cycle(self):
        """Testa criação de informação de ciclo."""
        cycle = CycleInfo(
            nodes=["class:A", "class:B", "class:C"],
            suggested_break="class:A"
        )
        assert len(cycle.nodes) == 3
        assert cycle.suggested_break == "class:A"

    def test_cycle_str(self):
        """Testa representação string do ciclo."""
        cycle = CycleInfo(
            nodes=["A", "B", "C"],
            suggested_break="B"
        )
        assert "A → B → C → A" in str(cycle)


class TestAnalysisResult:
    """Testes para AnalysisResult model."""

    def test_empty_result(self):
        """Testa resultado vazio."""
        result = AnalysisResult()
        assert result.total_nodes == 0
        assert result.total_edges == 0
        assert result.has_cycles is False
        assert result.topological_order == []

    def test_result_with_cycles(self):
        """Testa resultado com ciclos."""
        result = AnalysisResult(
            total_nodes=10,
            cycles=[
                CycleInfo(nodes=["A", "B"], suggested_break="A")
            ]
        )
        assert result.has_cycles is True

    def test_get_summary(self):
        """Testa geração de resumo."""
        result = AnalysisResult(
            total_nodes=5,
            total_edges=3,
            nodes_by_type={"table": 2, "class": 3},
            edges_by_type={"uses_table": 3},
        )
        summary = result.get_summary()
        assert "Nodes: 5" in summary
        assert "Edges: 3" in summary
        assert "table: 2" in summary
        assert "class: 3" in summary


class TestCycleDetector:
    """Testes para CycleDetector."""

    def test_no_cycles(self):
        """Testa grafo sem ciclos."""
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("A", "C")

        detector = CycleDetector(graph)
        cycles = detector.detect_cycles()

        assert len(cycles) == 0
        assert detector.has_cycles is False

    def test_simple_cycle(self):
        """Testa detecção de ciclo simples."""
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")  # Ciclo!

        detector = CycleDetector(graph)
        cycles = detector.detect_cycles()

        assert len(cycles) == 1
        assert detector.has_cycles is True
        assert set(cycles[0].nodes) == {"A", "B", "C"}

    def test_multiple_cycles(self):
        """Testa detecção de múltiplos ciclos."""
        graph = nx.DiGraph()
        # Ciclo 1: A → B → A
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")
        # Ciclo 2: C → D → C
        graph.add_edge("C", "D")
        graph.add_edge("D", "C")

        detector = CycleDetector(graph)
        cycles = detector.detect_cycles()

        assert len(cycles) >= 2
        assert detector.cycle_count >= 2

    def test_find_best_break_point(self):
        """Testa seleção de ponto de quebra."""
        graph = nx.DiGraph()
        # A tem mais dependentes (out-degree maior)
        graph.add_edge("A", "B")
        graph.add_edge("A", "C")
        graph.add_edge("B", "A")

        detector = CycleDetector(graph)
        break_point = detector._find_best_break_point(["A", "B"])

        # A deve ser sugerido (score = in_degree - out_degree = 1 - 2 = -1)
        # B tem score = 1 - 1 = 0
        # Menor score é melhor (nó com mais dependentes)
        assert break_point == "A"

    def test_remove_cycle_edges(self):
        """Testa remoção de arestas para eliminar ciclos."""
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")

        detector = CycleDetector(graph)
        acyclic = detector.remove_cycle_edges()

        assert nx.is_directed_acyclic_graph(acyclic)
        assert acyclic.number_of_edges() < graph.number_of_edges()

    def test_get_cycle_report(self):
        """Testa geração de relatório de ciclos."""
        graph = nx.DiGraph()
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")

        detector = CycleDetector(graph)
        detector.detect_cycles()
        report = detector.get_cycle_report()

        assert "Ciclos Detectados: 1" in report
        assert "Ciclo 1:" in report

    def test_get_cycle_report_no_cycles(self):
        """Testa relatório quando não há ciclos."""
        graph = nx.DiGraph()
        graph.add_edge("A", "B")

        detector = CycleDetector(graph)
        detector.detect_cycles()
        report = detector.get_cycle_report()

        assert "Nenhum ciclo detectado" in report

    def test_strongly_connected_components(self):
        """Testa detecção de componentes fortemente conectados."""
        graph = nx.DiGraph()
        # SCC: A, B, C
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")
        graph.add_edge("C", "A")
        # Nó isolado
        graph.add_edge("D", "E")

        detector = CycleDetector(graph)
        sccs = detector.get_strongly_connected_components()

        assert len(sccs) == 1
        assert {"A", "B", "C"} in sccs


class TestTopologicalSorter:
    """Testes para TopologicalSorter."""

    def test_simple_sort(self):
        """Testa ordenação simples."""
        graph = nx.DiGraph()
        graph.add_node("A", node_type="table", layer="schema")
        graph.add_node("B", node_type="class", layer="domain")
        graph.add_node("C", node_type="procedure", layer="business")
        graph.add_edge("C", "B")
        graph.add_edge("B", "A")

        sorter = TopologicalSorter(graph)
        order = sorter.sort()

        # Schema deve vir antes de domain, que deve vir antes de business
        assert order.index("A") < order.index("B")
        assert order.index("B") < order.index("C")

    def test_layer_grouping(self):
        """Testa agrupamento por camadas."""
        graph = nx.DiGraph()
        graph.add_node("T1", node_type="table", layer="schema")
        graph.add_node("T2", node_type="table", layer="schema")
        graph.add_node("C1", node_type="class", layer="domain")
        graph.add_node("P1", node_type="page", layer="ui")

        sorter = TopologicalSorter(graph)
        sorter.sort()
        layers = sorter.get_layers()

        assert "T1" in layers["schema"]
        assert "T2" in layers["schema"]
        assert "C1" in layers["domain"]
        assert "P1" in layers["ui"]

    def test_handles_cycles(self):
        """Testa que sorter lida com ciclos."""
        graph = nx.DiGraph()
        graph.add_node("A", node_type="class", layer="domain")
        graph.add_node("B", node_type="class", layer="domain")
        graph.add_edge("A", "B")
        graph.add_edge("B", "A")  # Ciclo!

        sorter = TopologicalSorter(graph)
        order = sorter.sort()

        # Deve retornar ordenação mesmo com ciclo
        assert len(order) == 2
        assert "A" in order
        assert "B" in order

    def test_get_node_order(self):
        """Testa obtenção da posição de um nó."""
        graph = nx.DiGraph()
        graph.add_node("A", node_type="table", layer="schema")
        graph.add_node("B", node_type="class", layer="domain")
        graph.add_edge("B", "A")

        sorter = TopologicalSorter(graph)
        sorter.sort()

        assert sorter.get_node_order("A") == 0
        assert sorter.get_node_order("B") == 1
        assert sorter.get_node_order("X") is None

    def test_get_layer_for_node(self):
        """Testa obtenção da camada de um nó."""
        graph = nx.DiGraph()
        graph.add_node("T1", node_type="table", layer="schema")
        graph.add_node("P1", node_type="page", layer="ui")

        sorter = TopologicalSorter(graph)
        sorter.sort()

        assert sorter.get_layer_for_node("T1") == "schema"
        assert sorter.get_layer_for_node("P1") == "ui"
        assert sorter.get_layer_for_node("X") is None

    def test_layer_stats(self):
        """Testa estatísticas por camada."""
        graph = nx.DiGraph()
        graph.add_node("T1", node_type="table", layer="schema")
        graph.add_node("T2", node_type="table", layer="schema")
        graph.add_node("C1", node_type="class", layer="domain")

        sorter = TopologicalSorter(graph)
        sorter.sort()
        stats = sorter.get_layer_stats()

        schema_stat = next(s for s in stats if s.layer == ElementLayer.SCHEMA)
        assert schema_stat.count == 2
        assert schema_stat.order_start == 0
        assert schema_stat.order_end == 1

    def test_alphabetical_stable_sort(self):
        """Testa ordenação alfabética estável dentro de camada."""
        graph = nx.DiGraph()
        graph.add_node("C", node_type="table", layer="schema")
        graph.add_node("A", node_type="table", layer="schema")
        graph.add_node("B", node_type="table", layer="schema")

        sorter = TopologicalSorter(graph)
        order = sorter.sort()

        # Sem dependências, devem estar em ordem alfabética
        schema_nodes = [n for n in order if n in ["A", "B", "C"]]
        assert schema_nodes == ["A", "B", "C"]

    def test_empty_graph(self):
        """Testa grafo vazio."""
        graph = nx.DiGraph()

        sorter = TopologicalSorter(graph)
        order = sorter.sort()

        assert order == []
        assert sorter.get_layers() == {
            "schema": [],
            "domain": [],
            "business": [],
            "api": [],
            "ui": []
        }


class TestLayerStats:
    """Testes para LayerStats model."""

    def test_create_layer_stats(self):
        """Testa criação de estatísticas de camada."""
        stats = LayerStats(
            layer=ElementLayer.SCHEMA,
            count=5,
            order_start=0,
            order_end=4
        )
        assert stats.layer == ElementLayer.SCHEMA
        assert stats.count == 5
        assert stats.order_start == 0
        assert stats.order_end == 4


class TestIntegration:
    """Testes de integração entre componentes."""

    def test_full_analysis_pipeline(self):
        """Testa pipeline completo de análise."""
        # Cria grafo simulando projeto real
        graph = nx.DiGraph()

        # Tabelas (schema)
        graph.add_node("table:CLIENTE", node_type="table", layer="schema")
        graph.add_node("table:PEDIDO", node_type="table", layer="schema")

        # Classes (domain)
        graph.add_node("class:Cliente", node_type="class", layer="domain")
        graph.add_node("class:Pedido", node_type="class", layer="domain")

        # Procedures (business)
        graph.add_node("proc:CadastrarCliente", node_type="procedure", layer="business")
        graph.add_node("proc:CriarPedido", node_type="procedure", layer="business")

        # Páginas (ui)
        graph.add_node("page:PAGE_Cliente", node_type="page", layer="ui")
        graph.add_node("page:PAGE_Pedido", node_type="page", layer="ui")

        # Dependências
        graph.add_edge("class:Cliente", "table:CLIENTE")
        graph.add_edge("class:Pedido", "table:PEDIDO")
        graph.add_edge("class:Pedido", "class:Cliente")  # Pedido usa Cliente
        graph.add_edge("proc:CadastrarCliente", "class:Cliente")
        graph.add_edge("proc:CriarPedido", "class:Pedido")
        graph.add_edge("page:PAGE_Cliente", "proc:CadastrarCliente")
        graph.add_edge("page:PAGE_Pedido", "proc:CriarPedido")

        # Detecta ciclos
        detector = CycleDetector(graph)
        cycles = detector.detect_cycles()
        assert len(cycles) == 0

        # Ordena
        sorter = TopologicalSorter(graph)
        order = sorter.sort()

        # Verifica ordem das camadas
        tables = [n for n in order if n.startswith("table:")]
        classes = [n for n in order if n.startswith("class:")]
        procs = [n for n in order if n.startswith("proc:")]
        pages = [n for n in order if n.startswith("page:")]

        # Tabelas devem vir primeiro
        assert all(order.index(t) < order.index(c) for t in tables for c in classes)
        # Classes antes de procedures
        assert all(order.index(c) < order.index(p) for c in classes for p in procs)
        # Procedures antes de páginas
        assert all(order.index(p) < order.index(pg) for p in procs for pg in pages)
