"""
Analisador de dependências - orquestrador principal.

Coordena GraphBuilder, CycleDetector e TopologicalSorter
para análise completa de dependências do projeto.
"""

import logging
from typing import Optional

import networkx as nx
from beanie import PydanticObjectId

from wxcode.analyzer.cycle_detector import CycleDetector
from wxcode.analyzer.graph_builder import GraphBuilder
from wxcode.analyzer.models import AnalysisResult
from wxcode.analyzer.topological_sorter import TopologicalSorter
from wxcode.models import ClassDefinition, Element, Procedure
from wxcode.models.schema import DatabaseSchema

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """
    Orquestrador de análise de dependências.

    Coordena:
    1. Construção do grafo (GraphBuilder)
    2. Detecção de ciclos (CycleDetector)
    3. Ordenação topológica (TopologicalSorter)
    4. Persistência no MongoDB
    """

    def __init__(self, project_id: PydanticObjectId):
        """
        Inicializa o analisador.

        Args:
            project_id: ID do projeto no MongoDB
        """
        self.project_id = project_id
        self.graph: Optional[nx.DiGraph] = None
        self._result: Optional[AnalysisResult] = None

    async def analyze(self, persist: bool = True) -> AnalysisResult:
        """
        Executa análise completa de dependências.

        Args:
            persist: Se True, persiste ordem no MongoDB

        Returns:
            AnalysisResult com estatísticas e ordem
        """
        logger.info(f"Iniciando análise de dependências para projeto {self.project_id}")

        # 1. Constrói o grafo
        builder = GraphBuilder(self.project_id)
        self.graph = await builder.build()

        logger.info(
            f"Grafo construído: {self.graph.number_of_nodes()} nós, "
            f"{self.graph.number_of_edges()} arestas"
        )

        # 2. Detecta ciclos
        detector = CycleDetector(self.graph)
        cycles = detector.detect_cycles()

        if cycles:
            logger.warning(f"Detectados {len(cycles)} ciclos")
            for cycle in cycles[:5]:  # Mostra até 5 ciclos
                logger.warning(f"  Ciclo: {' → '.join(cycle.nodes)}")

        # 3. Ordena topologicamente
        sorter = TopologicalSorter(self.graph)
        order = sorter.sort()
        layers = sorter.get_layers()
        layer_stats = sorter.get_layer_stats()

        # 4. Monta resultado
        self._result = AnalysisResult(
            total_nodes=self.graph.number_of_nodes(),
            total_edges=self.graph.number_of_edges(),
            nodes_by_type=builder.get_node_count_by_type(),
            edges_by_type=builder.get_edge_count_by_type(),
            cycles=cycles,
            topological_order=order,
            layer_stats=layer_stats,
            layers=layers
        )

        # 5. Persiste no MongoDB
        if persist:
            await self._persist_order(order, layers)

        logger.info("Análise de dependências concluída")
        return self._result

    async def _persist_order(
        self,
        order: list[str],
        layers: dict[str, list[str]]
    ) -> None:
        """
        Persiste ordem topológica nos documentos MongoDB.

        Args:
            order: Lista ordenada de node IDs
            layers: Nós agrupados por camada
        """
        # Cria mapeamento node_id → (order, layer)
        node_info: dict[str, tuple[int, str]] = {}

        for layer_name, nodes in layers.items():
            for node_id in nodes:
                try:
                    pos = order.index(node_id)
                    node_info[node_id] = (pos, layer_name)
                except ValueError:
                    pass

        updated_elements = 0
        updated_classes = 0
        updated_procedures = 0

        # Atualiza Elements (pages, windows)
        for node_id, (pos, layer) in node_info.items():
            if node_id.startswith("page:"):
                name = node_id.split(":", 1)[1]
                result = await Element.find(
                    {"project_id.$id": self.project_id, "source_name": name}
                ).update_many(
                    {"$set": {"topological_order": pos, "layer": layer}}
                )
                updated_elements += result.modified_count

        # Atualiza Classes (usa project_id direto, não DBRef)
        for node_id, (pos, layer) in node_info.items():
            if node_id.startswith("class:"):
                name = node_id.split(":", 1)[1]
                result = await ClassDefinition.find(
                    {"project_id": self.project_id, "name": name}
                ).update_many(
                    {"$set": {"topological_order": pos, "layer": layer}}
                )
                updated_classes += result.modified_count

        # Atualiza Procedures (usa project_id direto, não DBRef)
        for node_id, (pos, layer) in node_info.items():
            if node_id.startswith("proc:"):
                name = node_id.split(":", 1)[1]
                result = await Procedure.find(
                    {"project_id": self.project_id, "name": name}
                ).update_many(
                    {"$set": {"topological_order": pos, "layer": layer}}
                )
                updated_procedures += result.modified_count

        # Atualiza Tables no DatabaseSchema (embedded documents)
        updated_tables = 0
        schema = await DatabaseSchema.find_one(
            DatabaseSchema.project_id == self.project_id
        )
        if schema:
            tables_updated = False
            for table in schema.tables:
                table_node_id = f"table:{table.name}"
                if table_node_id in node_info:
                    pos, layer = node_info[table_node_id]
                    table.topological_order = pos
                    table.layer = layer
                    updated_tables += 1
                    tables_updated = True

            if tables_updated:
                await schema.save()

        logger.info(
            f"Persistidos: {updated_elements} elements, "
            f"{updated_classes} classes, {updated_procedures} procedures, "
            f"{updated_tables} tables"
        )

    def get_result(self) -> Optional[AnalysisResult]:
        """Retorna resultado da última análise."""
        return self._result

    def get_graph(self) -> Optional[nx.DiGraph]:
        """Retorna grafo construído."""
        return self.graph

    async def get_dependencies_for(self, node_id: str) -> dict:
        """
        Retorna dependências de um nó específico.

        Args:
            node_id: ID do nó (ex: "class:Usuario")

        Returns:
            Dict com predecessors e successors
        """
        if not self.graph:
            await self.analyze(persist=False)

        if node_id not in self.graph:
            return {"error": f"Nó não encontrado: {node_id}"}

        return {
            "node": node_id,
            "depends_on": list(self.graph.predecessors(node_id)),
            "depended_by": list(self.graph.successors(node_id)),
            "in_degree": self.graph.in_degree(node_id),
            "out_degree": self.graph.out_degree(node_id),
        }

    async def get_impact_analysis(self, node_id: str) -> dict:
        """
        Analisa impacto de mudanças em um nó.

        Retorna todos os nós que seriam afetados
        por mudanças no nó especificado.

        Args:
            node_id: ID do nó

        Returns:
            Dict com nós impactados por camada
        """
        if not self.graph:
            await self.analyze(persist=False)

        if node_id not in self.graph:
            return {"error": f"Nó não encontrado: {node_id}"}

        # Todos os nós que dependem deste (direta ou indiretamente)
        descendants = nx.descendants(self.graph, node_id)

        # Agrupa por camada
        impact: dict[str, list[str]] = {}
        for desc in descendants:
            data = self.graph.nodes[desc]
            layer = data.get("layer", "unknown")
            if layer not in impact:
                impact[layer] = []
            impact[layer].append(desc)

        return {
            "node": node_id,
            "total_impacted": len(descendants),
            "impacted_by_layer": impact,
        }

    def export_dot(self) -> str:
        """
        Exporta grafo no formato DOT (Graphviz).

        Returns:
            String no formato DOT
        """
        if not self.graph:
            return ""

        from io import StringIO
        output = StringIO()

        output.write("digraph dependencies {\n")
        output.write("  rankdir=LR;\n")
        output.write("  node [shape=box];\n\n")

        # Agrupa nós por camada
        layers: dict[str, list[str]] = {}
        for node_id, data in self.graph.nodes(data=True):
            layer = data.get("layer", "unknown")
            if layer not in layers:
                layers[layer] = []
            layers[layer].append(node_id)

        # Cria subgrafos por camada
        for layer, nodes in layers.items():
            output.write(f"  subgraph cluster_{layer} {{\n")
            output.write(f'    label="{layer}";\n')
            for node in nodes:
                # Escapa aspas no nome
                safe_node = node.replace('"', '\\"')
                output.write(f'    "{safe_node}";\n')
            output.write("  }\n\n")

        # Adiciona arestas
        for source, target, data in self.graph.edges(data=True):
            edge_type = data.get("edge_type", "")
            safe_source = source.replace('"', '\\"')
            safe_target = target.replace('"', '\\"')
            output.write(f'  "{safe_source}" -> "{safe_target}"')
            if edge_type:
                output.write(f' [label="{edge_type}"]')
            output.write(";\n")

        output.write("}\n")
        return output.getvalue()
