"""
Detector de ciclos no grafo de dependências.

Identifica ciclos que impedem ordenação topológica e sugere
pontos de quebra para resolver dependências circulares.
"""

import logging
from typing import Optional

import networkx as nx

from wxcode.analyzer.models import CycleInfo

logger = logging.getLogger(__name__)


class CycleDetector:
    """
    Detecta ciclos em um grafo de dependências.

    Ciclos impedem ordenação topológica e precisam ser
    identificados para conversão em camadas.
    """

    def __init__(self, graph: nx.DiGraph):
        """
        Inicializa o detector.

        Args:
            graph: Grafo NetworkX dirigido
        """
        self.graph = graph
        self._cycles: list[CycleInfo] = []

    def detect_cycles(self) -> list[CycleInfo]:
        """
        Detecta todos os ciclos no grafo.

        Usa algoritmo de Johnson para encontrar ciclos simples.

        Returns:
            Lista de CycleInfo com ciclos detectados
        """
        self._cycles = []

        try:
            # Encontra todos os ciclos simples
            raw_cycles = list(nx.simple_cycles(self.graph))
        except nx.NetworkXError as e:
            logger.error(f"Erro ao detectar ciclos: {e}")
            return []

        if not raw_cycles:
            logger.info("Nenhum ciclo detectado no grafo")
            return []

        # Processa cada ciclo
        for cycle_nodes in raw_cycles:
            if len(cycle_nodes) < 2:
                continue

            # Encontra melhor ponto de quebra
            break_point = self._find_best_break_point(cycle_nodes)

            cycle_info = CycleInfo(
                nodes=cycle_nodes,
                suggested_break=break_point
            )
            self._cycles.append(cycle_info)

        logger.warning(f"Detectados {len(self._cycles)} ciclos no grafo")
        return self._cycles

    def _find_best_break_point(self, cycle_nodes: list[str]) -> str:
        """
        Encontra o melhor nó para quebrar o ciclo.

        Critérios (em ordem de prioridade):
        1. Menor in-degree (menos dependências)
        2. Maior out-degree (mais dependentes)
        3. Primeiro alfabeticamente

        Args:
            cycle_nodes: Nós no ciclo

        Returns:
            ID do nó sugerido para quebra
        """
        if not cycle_nodes:
            return ""

        best_node = cycle_nodes[0]
        best_score = float('inf')

        for node in cycle_nodes:
            # Score: in-degree - out-degree (menor é melhor)
            in_deg = self.graph.in_degree(node)
            out_deg = self.graph.out_degree(node)
            score = in_deg - out_deg

            if score < best_score:
                best_score = score
                best_node = node
            elif score == best_score and node < best_node:
                # Desempate alfabético
                best_node = node

        return best_node

    def get_cycle_report(self) -> str:
        """
        Gera relatório formatado dos ciclos.

        Returns:
            Relatório em texto
        """
        if not self._cycles:
            return "Nenhum ciclo detectado."

        lines = [
            f"Ciclos Detectados: {len(self._cycles)}",
            "=" * 40
        ]

        for i, cycle in enumerate(self._cycles, 1):
            cycle_path = " → ".join(cycle.nodes)
            lines.append(f"\nCiclo {i}:")
            lines.append(f"  Caminho: {cycle_path} → {cycle.nodes[0]}")
            lines.append(f"  Sugestão de quebra: {cycle.suggested_break}")

        return "\n".join(lines)

    def remove_cycle_edges(self) -> nx.DiGraph:
        """
        Cria cópia do grafo removendo arestas que causam ciclos.

        Remove a aresta que entra no nó sugerido para quebra
        de cada ciclo detectado.

        Returns:
            Novo grafo sem ciclos
        """
        # Cria cópia do grafo
        acyclic = self.graph.copy()

        # Detecta ciclos se ainda não detectou
        if not self._cycles:
            self.detect_cycles()

        edges_removed = 0

        for cycle in self._cycles:
            break_node = cycle.suggested_break
            nodes = cycle.nodes

            # Encontra a aresta que entra no break_node
            break_idx = nodes.index(break_node)
            prev_idx = (break_idx - 1) % len(nodes)
            prev_node = nodes[prev_idx]

            # Remove a aresta se existir
            if acyclic.has_edge(prev_node, break_node):
                acyclic.remove_edge(prev_node, break_node)
                edges_removed += 1
                logger.debug(f"Removida aresta: {prev_node} → {break_node}")

        logger.info(f"Removidas {edges_removed} arestas para eliminar ciclos")

        # Verifica se ainda há ciclos
        if not nx.is_directed_acyclic_graph(acyclic):
            logger.warning("Grafo ainda contém ciclos após remoção")

        return acyclic

    def get_strongly_connected_components(self) -> list[set[str]]:
        """
        Retorna componentes fortemente conectados.

        Componentes com mais de 1 nó indicam ciclos.

        Returns:
            Lista de conjuntos de nós
        """
        sccs = list(nx.strongly_connected_components(self.graph))
        # Filtra apenas componentes com ciclos (mais de 1 nó)
        return [scc for scc in sccs if len(scc) > 1]

    @property
    def has_cycles(self) -> bool:
        """Verifica se o grafo tem ciclos."""
        return not nx.is_directed_acyclic_graph(self.graph)

    @property
    def cycle_count(self) -> int:
        """Retorna número de ciclos detectados."""
        if not self._cycles:
            self.detect_cycles()
        return len(self._cycles)
