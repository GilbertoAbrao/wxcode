"""
Construtor do grafo de dependências.

Carrega dados do MongoDB e constrói um grafo NetworkX
com nós e arestas representando dependências.
"""

import logging
from typing import Optional

import networkx as nx
from beanie import PydanticObjectId

from wxcode.analyzer.models import EdgeType, GraphNode, NodeType
from wxcode.models import (
    ClassDefinition,
    DatabaseSchema,
    Element,
    ElementLayer,
    ElementType,
    Procedure,
)

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Constrói grafo de dependências a partir dos dados do MongoDB.

    Cria nós para:
    - Tabelas (schema)
    - Classes (domain)
    - Procedures (business)
    - Páginas/Windows (ui)

    Cria arestas para:
    - Herança de classes
    - Uso de classes
    - Chamadas de procedures
    - Acesso a tabelas
    """

    def __init__(self, project_id: PydanticObjectId):
        """
        Inicializa o builder.

        Args:
            project_id: ID do projeto no MongoDB
        """
        self.project_id = project_id
        self.graph = nx.DiGraph()
        self._node_registry: dict[str, GraphNode] = {}

    async def build(self) -> nx.DiGraph:
        """
        Constrói o grafo completo de dependências.

        Returns:
            NetworkX DiGraph com nós e arestas
        """
        # 1. Adiciona tabelas (schema)
        await self._add_table_nodes()

        # 2. Adiciona classes (domain)
        await self._add_class_nodes()

        # 3. Adiciona procedures (business)
        await self._add_procedure_nodes()

        # 4. Adiciona páginas/windows (ui)
        await self._add_page_nodes()

        return self.graph

    async def _add_table_nodes(self) -> None:
        """Adiciona nós de tabelas do schema."""
        # DatabaseSchema usa ObjectId direto (não DBRef)
        schema = await DatabaseSchema.find_one({
            "project_id": self.project_id
        })

        if not schema:
            logger.warning("Schema não encontrado para o projeto")
            return

        for table in schema.tables:
            node_id = f"table:{table.name}"
            node = GraphNode(
                id=node_id,
                name=table.name,
                node_type=NodeType.TABLE,
                layer=ElementLayer.SCHEMA,
                collection="schemas"
            )
            self._add_node(node)

        logger.info(f"Adicionadas {len(schema.tables)} tabelas")

    async def _add_class_nodes(self) -> None:
        """Adiciona nós e arestas de classes."""
        # ClassDefinition usa ObjectId direto (não DBRef)
        classes = await ClassDefinition.find({
            "project_id": self.project_id
        }).to_list()

        # Primeiro, adiciona todos os nós
        for cls in classes:
            node_id = f"class:{cls.name}"
            node = GraphNode(
                id=node_id,
                name=cls.name,
                node_type=NodeType.CLASS,
                layer=ElementLayer.DOMAIN,
                mongo_id=cls.id,
                collection="classes"
            )
            self._add_node(node)

        # Depois, adiciona arestas
        for cls in classes:
            source_id = f"class:{cls.name}"

            # Herança
            if cls.inherits_from:
                target_id = f"class:{cls.inherits_from}"
                self._add_edge(source_id, target_id, EdgeType.INHERITS)

            # Uso de classes
            if cls.dependencies and cls.dependencies.uses_classes:
                for used_class in cls.dependencies.uses_classes:
                    target_id = f"class:{used_class}"
                    self._add_edge(source_id, target_id, EdgeType.USES_CLASS)

            # Uso de tabelas
            if cls.dependencies and cls.dependencies.uses_files:
                for table in cls.dependencies.uses_files:
                    target_id = f"table:{table}"
                    self._add_edge(source_id, target_id, EdgeType.USES_TABLE)

        logger.info(f"Adicionadas {len(classes)} classes")

    async def _add_procedure_nodes(self) -> None:
        """Adiciona nós e arestas de procedures."""
        # Procedure usa ObjectId direto (não DBRef)
        procedures = await Procedure.find({
            "project_id": self.project_id
        }).to_list()

        # Cria um set de nomes de procedures para validação
        proc_names = {p.name for p in procedures}

        # Primeiro, adiciona todos os nós
        for proc in procedures:
            node_id = f"proc:{proc.name}"
            node = GraphNode(
                id=node_id,
                name=proc.name,
                node_type=NodeType.PROCEDURE,
                layer=ElementLayer.BUSINESS,
                mongo_id=proc.id,
                collection="procedures"
            )
            self._add_node(node)

        # Depois, adiciona arestas
        for proc in procedures:
            source_id = f"proc:{proc.name}"

            # Chamadas de outras procedures
            if proc.dependencies and proc.dependencies.calls_procedures:
                for called in proc.dependencies.calls_procedures:
                    # Ignora auto-recursão
                    if called == proc.name:
                        continue

                    # Só adiciona se a procedure existir no projeto
                    if called in proc_names:
                        target_id = f"proc:{called}"
                        self._add_edge(source_id, target_id, EdgeType.CALLS_PROCEDURE)

            # Uso de tabelas
            if proc.dependencies and proc.dependencies.uses_files:
                for table in proc.dependencies.uses_files:
                    target_id = f"table:{table}"
                    self._add_edge(source_id, target_id, EdgeType.USES_TABLE)

        logger.info(f"Adicionadas {len(procedures)} procedures")

    async def _add_page_nodes(self) -> None:
        """Adiciona nós e arestas de páginas/windows."""
        # Busca páginas e windows
        elements = await Element.find({
            "project_id.$id": self.project_id,
            "source_type": {"$in": [
                ElementType.PAGE.value,
                ElementType.WINDOW.value,
            ]}
        }).to_list()

        # Cria sets para validação
        proc_names = {n.split(":")[1] for n in self._node_registry if n.startswith("proc:")}
        class_names = {n.split(":")[1] for n in self._node_registry if n.startswith("class:")}

        # Primeiro, adiciona todos os nós
        for elem in elements:
            node_type = NodeType.PAGE if elem.source_type == ElementType.PAGE else NodeType.WINDOW
            node_id = f"page:{elem.source_name}"
            node = GraphNode(
                id=node_id,
                name=elem.source_name,
                node_type=node_type,
                layer=ElementLayer.UI,
                mongo_id=elem.id,
                collection="elements"
            )
            self._add_node(node)

        # Depois, adiciona arestas
        for elem in elements:
            source_id = f"page:{elem.source_name}"

            if not elem.dependencies:
                continue

            # Dependências de procedures e classes
            for dep in elem.dependencies.uses:
                if not dep:
                    continue

                # Verifica se é classe ou procedure
                if dep.startswith("class") or dep in class_names:
                    target_id = f"class:{dep}"
                    if dep in class_names:
                        self._add_edge(source_id, target_id, EdgeType.USES_CLASS)
                elif dep in proc_names:
                    target_id = f"proc:{dep}"
                    self._add_edge(source_id, target_id, EdgeType.CALLS_PROCEDURE)

            # Dependências de tabelas
            for table in elem.dependencies.data_files:
                target_id = f"table:{table}"
                self._add_edge(source_id, target_id, EdgeType.USES_TABLE)

        logger.info(f"Adicionadas {len(elements)} páginas/windows")

    def _add_node(self, node: GraphNode) -> None:
        """
        Adiciona um nó ao grafo.

        Args:
            node: Nó a adicionar
        """
        if node.id in self._node_registry:
            return  # Nó já existe

        self._node_registry[node.id] = node
        self.graph.add_node(
            node.id,
            name=node.name,
            node_type=node.node_type.value,
            layer=node.layer.value,
            mongo_id=str(node.mongo_id) if node.mongo_id else None,
            collection=node.collection
        )

    def _add_edge(
        self,
        source: str,
        target: str,
        edge_type: EdgeType
    ) -> None:
        """
        Adiciona uma aresta ao grafo.

        Args:
            source: ID do nó de origem
            target: ID do nó de destino
            edge_type: Tipo da aresta
        """
        # Só adiciona se o destino existir
        if target not in self._node_registry:
            logger.debug(f"Dependência não encontrada: {source} → {target}")
            return

        # Evita duplicatas
        if self.graph.has_edge(source, target):
            return

        self.graph.add_edge(
            source,
            target,
            edge_type=edge_type.value
        )

    def get_node_count_by_type(self) -> dict[str, int]:
        """Retorna contagem de nós por tipo."""
        counts: dict[str, int] = {}
        for node_id, data in self.graph.nodes(data=True):
            node_type = data.get("node_type", "unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def get_edge_count_by_type(self) -> dict[str, int]:
        """Retorna contagem de arestas por tipo."""
        counts: dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            edge_type = data.get("edge_type", "unknown")
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts
