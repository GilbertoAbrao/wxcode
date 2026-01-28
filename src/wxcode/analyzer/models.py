"""
Models para análise de dependências.

Define estruturas para representar nós, arestas e resultados
da análise do grafo de dependências.
"""

from enum import Enum
from typing import Optional

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from wxcode.models.element import ElementLayer


class NodeType(str, Enum):
    """Tipo de nó no grafo de dependências."""
    TABLE = "table"
    CLASS = "class"
    PROCEDURE = "procedure"
    PAGE = "page"
    WINDOW = "window"
    QUERY = "query"


class EdgeType(str, Enum):
    """Tipo de aresta no grafo de dependências."""
    INHERITS = "inherits"           # Class → Class (herança)
    USES_CLASS = "uses_class"       # Any → Class
    CALLS_PROCEDURE = "calls_proc"  # Any → Procedure
    USES_TABLE = "uses_table"       # Any → Table
    USES_QUERY = "uses_query"       # Any → Query


class GraphNode(BaseModel):
    """
    Nó no grafo de dependências.

    Representa uma entidade do projeto (tabela, classe, procedure, página).
    """

    id: str = Field(..., description="ID único (tipo:nome)")
    name: str = Field(..., description="Nome de exibição")
    node_type: NodeType = Field(..., description="Tipo do nó")
    layer: ElementLayer = Field(..., description="Camada de conversão")
    mongo_id: Optional[PydanticObjectId] = Field(
        default=None,
        description="ID do documento no MongoDB"
    )
    collection: Optional[str] = Field(
        default=None,
        description="Nome da collection no MongoDB"
    )

    def __str__(self) -> str:
        return f"{self.node_type.value}:{self.name}"


class GraphEdge(BaseModel):
    """
    Aresta no grafo de dependências.

    Representa uma dependência entre dois nós.
    """

    source: str = Field(..., description="ID do nó de origem")
    target: str = Field(..., description="ID do nó de destino")
    edge_type: EdgeType = Field(..., description="Tipo da dependência")
    weight: int = Field(default=1, description="Peso da aresta")

    def __str__(self) -> str:
        return f"{self.source} --[{self.edge_type.value}]--> {self.target}"


class CycleInfo(BaseModel):
    """
    Informação sobre um ciclo detectado no grafo.

    Ciclos impedem ordenação topológica e precisam ser resolvidos.
    """

    nodes: list[str] = Field(..., description="Nós no ciclo")
    suggested_break: str = Field(
        ...,
        description="Nó sugerido para quebrar o ciclo"
    )

    def __str__(self) -> str:
        cycle_str = " → ".join(self.nodes)
        return f"Ciclo: {cycle_str} → {self.nodes[0]}"


class LayerStats(BaseModel):
    """Estatísticas por camada."""

    layer: ElementLayer
    count: int
    order_start: int
    order_end: int


class AnalysisResult(BaseModel):
    """
    Resultado completo da análise de dependências.

    Contém estatísticas, ciclos detectados e ordem topológica.
    """

    # Estatísticas gerais
    total_nodes: int = Field(default=0, description="Total de nós")
    total_edges: int = Field(default=0, description="Total de arestas")

    # Contagem por tipo
    nodes_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Nós por tipo"
    )
    edges_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Arestas por tipo"
    )

    # Ciclos
    cycles: list[CycleInfo] = Field(
        default_factory=list,
        description="Ciclos detectados"
    )

    @property
    def has_cycles(self) -> bool:
        """Verifica se há ciclos."""
        return len(self.cycles) > 0

    # Ordem topológica
    topological_order: list[str] = Field(
        default_factory=list,
        description="Nós em ordem topológica"
    )

    # Estatísticas por camada
    layer_stats: list[LayerStats] = Field(
        default_factory=list,
        description="Estatísticas por camada"
    )

    # Nós por camada
    layers: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Nós agrupados por camada"
    )

    def get_summary(self) -> str:
        """Retorna resumo formatado."""
        lines = [
            f"Nodes: {self.total_nodes}",
        ]
        for node_type, count in self.nodes_by_type.items():
            lines.append(f"  - {node_type}: {count}")

        lines.append(f"\nEdges: {self.total_edges}")
        for edge_type, count in self.edges_by_type.items():
            lines.append(f"  - {edge_type}: {count}")

        if self.has_cycles:
            lines.append(f"\nCycles Detected: {len(self.cycles)}")
            for cycle in self.cycles:
                lines.append(f"  ⚠ {cycle}")
        else:
            lines.append("\nNo cycles detected ✓")

        return "\n".join(lines)
