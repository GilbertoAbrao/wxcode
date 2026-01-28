"""
Ordenação topológica do grafo de dependências.

Ordena os elementos respeitando:
1. Dependências entre elementos
2. Hierarquia de camadas (schema → domain → business → ui)
"""

import logging
from typing import Optional

import networkx as nx

from wxcode.analyzer.cycle_detector import CycleDetector
from wxcode.analyzer.models import LayerStats, NodeType
from wxcode.models.element import ElementLayer

logger = logging.getLogger(__name__)

# Mapeamento de NodeType para ElementLayer
NODE_TYPE_TO_LAYER = {
    NodeType.TABLE: ElementLayer.SCHEMA,
    NodeType.CLASS: ElementLayer.DOMAIN,
    NodeType.PROCEDURE: ElementLayer.BUSINESS,
    NodeType.PAGE: ElementLayer.UI,
    NodeType.WINDOW: ElementLayer.UI,
    NodeType.QUERY: ElementLayer.DOMAIN,
}

# Ordem das camadas para conversão
LAYER_ORDER = [
    ElementLayer.SCHEMA,
    ElementLayer.DOMAIN,
    ElementLayer.BUSINESS,
    ElementLayer.API,
    ElementLayer.UI,
]


class TopologicalSorter:
    """
    Ordena elementos do grafo em ordem topológica.

    A ordenação respeita:
    1. Dependências entre elementos
    2. Hierarquia de camadas
    3. Ordem alfabética dentro de cada camada
    """

    def __init__(self, graph: nx.DiGraph):
        """
        Inicializa o sorter.

        Args:
            graph: Grafo NetworkX dirigido
        """
        self.graph = graph
        self._order: list[str] = []
        self._layers: dict[str, list[str]] = {}
        self._layer_stats: list[LayerStats] = []

    def sort(self) -> list[str]:
        """
        Ordena o grafo topologicamente.

        Se houver ciclos, usa CycleDetector para criar
        versão acíclica do grafo.

        Returns:
            Lista de node IDs em ordem de conversão
        """
        work_graph = self.graph

        # Verifica e trata ciclos
        if not nx.is_directed_acyclic_graph(self.graph):
            logger.warning("Grafo contém ciclos, removendo para ordenação")
            detector = CycleDetector(self.graph)
            work_graph = detector.remove_cycle_edges()

        # Atribui camadas aos nós
        self._assign_layers()

        # Ordena dentro de cada camada
        self._order = self._sort_with_layers(work_graph)

        # Calcula estatísticas
        self._compute_layer_stats()

        logger.info(f"Ordenação topológica: {len(self._order)} elementos")
        return self._order

    def _assign_layers(self) -> None:
        """Atribui camadas aos nós baseado no tipo."""
        self._layers = {layer.value: [] for layer in LAYER_ORDER}

        for node_id, data in self.graph.nodes(data=True):
            node_type_str = data.get("node_type", "unknown")
            layer_str = data.get("layer")

            # Usa layer do nó se disponível
            if layer_str:
                if layer_str not in self._layers:
                    self._layers[layer_str] = []
                self._layers[layer_str].append(node_id)
            else:
                # Infere layer pelo tipo do nó
                try:
                    node_type = NodeType(node_type_str)
                    layer = NODE_TYPE_TO_LAYER.get(node_type, ElementLayer.UI)
                    self._layers[layer.value].append(node_id)
                except ValueError:
                    # Tipo desconhecido vai para UI
                    self._layers[ElementLayer.UI.value].append(node_id)

    def _sort_with_layers(self, graph: nx.DiGraph) -> list[str]:
        """
        Ordena respeitando camadas e dependências.

        Args:
            graph: Grafo acíclico

        Returns:
            Lista ordenada de node IDs
        """
        result = []

        # Processa cada camada na ordem
        for layer in LAYER_ORDER:
            layer_nodes = self._layers.get(layer.value, [])
            if not layer_nodes:
                continue

            # Subgrafo da camada
            subgraph = graph.subgraph(layer_nodes).copy()

            # Ordena dentro da camada
            try:
                layer_order = list(nx.topological_sort(subgraph))
            except nx.NetworkXUnfeasible:
                # Se houver ciclo no subgrafo, ordena alfabeticamente
                logger.warning(f"Ciclo na camada {layer.value}, usando ordem alfabética")
                layer_order = sorted(layer_nodes)

            # Ordena alfabeticamente nós sem dependências entre si
            layer_order = self._stable_sort_within_layer(subgraph, layer_order)

            result.extend(layer_order)

        return result

    def _stable_sort_within_layer(
        self,
        subgraph: nx.DiGraph,
        order: list[str]
    ) -> list[str]:
        """
        Ordena alfabeticamente nós que não têm dependência entre si.

        Args:
            subgraph: Subgrafo da camada
            order: Ordem topológica inicial

        Returns:
            Ordem estabilizada
        """
        if len(order) <= 1:
            return order

        # Agrupa nós por "nível" (distância da raiz)
        levels: dict[int, list[str]] = {}

        for node in order:
            # Conta predecessores no subgrafo
            level = len(list(nx.ancestors(subgraph, node)))
            if level not in levels:
                levels[level] = []
            levels[level].append(node)

        # Ordena cada nível alfabeticamente
        result = []
        for level in sorted(levels.keys()):
            result.extend(sorted(levels[level]))

        return result

    def _compute_layer_stats(self) -> None:
        """Calcula estatísticas por camada."""
        self._layer_stats = []
        current_pos = 0

        for layer in LAYER_ORDER:
            layer_nodes = self._layers.get(layer.value, [])
            count = len(layer_nodes)

            if count > 0:
                stat = LayerStats(
                    layer=layer,
                    count=count,
                    order_start=current_pos,
                    order_end=current_pos + count - 1
                )
                self._layer_stats.append(stat)
                current_pos += count

    def get_conversion_order(self) -> list[str]:
        """
        Retorna ordem de conversão.

        Returns:
            Lista de node IDs na ordem de conversão
        """
        if not self._order:
            self.sort()
        return self._order

    def get_layers(self) -> dict[str, list[str]]:
        """
        Retorna nós agrupados por camada.

        Returns:
            Dict com layer → lista de node IDs
        """
        if not self._layers:
            self._assign_layers()
        return self._layers

    def get_layer_stats(self) -> list[LayerStats]:
        """
        Retorna estatísticas por camada.

        Returns:
            Lista de LayerStats
        """
        if not self._layer_stats:
            self._compute_layer_stats()
        return self._layer_stats

    def get_node_order(self, node_id: str) -> Optional[int]:
        """
        Retorna posição de um nó na ordem.

        Args:
            node_id: ID do nó

        Returns:
            Posição (0-indexed) ou None se não encontrado
        """
        if not self._order:
            self.sort()

        try:
            return self._order.index(node_id)
        except ValueError:
            return None

    def get_layer_for_node(self, node_id: str) -> Optional[str]:
        """
        Retorna camada de um nó.

        Args:
            node_id: ID do nó

        Returns:
            Nome da camada ou None
        """
        if not self._layers:
            self._assign_layers()

        for layer, nodes in self._layers.items():
            if node_id in nodes:
                return layer
        return None
