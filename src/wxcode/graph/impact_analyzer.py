"""
Análise de impacto usando Neo4j.
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

from wxcode.graph.neo4j_connection import Neo4jConnection

logger = logging.getLogger(__name__)


@dataclass
class AffectedNode:
    """Nó afetado por uma mudança."""

    name: str
    node_type: str
    depth: int


@dataclass
class ImpactResult:
    """Resultado da análise de impacto."""

    source_name: str
    source_type: str
    affected: list[AffectedNode] = field(default_factory=list)
    max_depth: int = 0
    error: Optional[str] = None

    @property
    def total_affected(self) -> int:
        """Total de elementos afetados."""
        return len(self.affected)

    def by_depth(self) -> dict[int, list[AffectedNode]]:
        """Agrupa afetados por profundidade."""
        result: dict[int, list[AffectedNode]] = {}
        for node in self.affected:
            if node.depth not in result:
                result[node.depth] = []
            result[node.depth].append(node)
        return result

    def by_type(self) -> dict[str, list[AffectedNode]]:
        """Agrupa afetados por tipo."""
        result: dict[str, list[AffectedNode]] = {}
        for node in self.affected:
            if node.node_type not in result:
                result[node.node_type] = []
            result[node.node_type].append(node)
        return result


@dataclass
class PathNode:
    """Nó em um caminho."""

    name: str
    node_type: str


@dataclass
class PathResult:
    """Resultado de busca de caminho."""

    source: str
    target: str
    paths: list[list[PathNode]] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def shortest_length(self) -> Optional[int]:
        """Comprimento do caminho mais curto."""
        if not self.paths:
            return None
        return min(len(p) for p in self.paths)


@dataclass
class HubNode:
    """Nó hub com muitas conexões."""

    name: str
    node_type: str
    incoming: int
    outgoing: int

    @property
    def total_connections(self) -> int:
        """Total de conexões."""
        return self.incoming + self.outgoing


@dataclass
class HubResult:
    """Resultado da busca por hubs."""

    min_connections: int
    hubs: list[HubNode] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class DeadCodeResult:
    """Resultado da busca por código morto."""

    procedures: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def total(self) -> int:
        """Total de elementos potencialmente não utilizados."""
        return len(self.procedures) + len(self.classes)


class ImpactAnalyzer:
    """
    Análise de impacto e queries de grafo usando Neo4j.

    Provê funções para:
    - Análise de impacto: o que é afetado se X mudar?
    - Busca de caminhos: como A se conecta a B?
    - Detecção de hubs: quais são os nós críticos?
    - Código morto: quais elementos não são utilizados?
    """

    def __init__(self, connection: Neo4jConnection):
        """
        Inicializa o analisador.

        Args:
            connection: Conexão Neo4j estabelecida
        """
        self.conn = connection

    async def get_impact(
        self,
        node_id: str,
        max_depth: int = 5,
        project: Optional[str] = None,
    ) -> ImpactResult:
        """
        Retorna todos os elementos afetados por mudança em node_id.

        Args:
            node_id: Identificador do nó (formato: TYPE:NAME ou apenas NAME)
            max_depth: Profundidade máxima de busca
            project: Filtrar por projeto (opcional)

        Returns:
            ImpactResult com lista de afetados

        Example:
            result = await analyzer.get_impact("TABLE:CLIENTE", max_depth=3)
        """
        # Parse node_id
        if ":" in node_id:
            node_type, name = node_id.split(":", 1)
            node_type = node_type.upper()
        else:
            node_type = None
            name = node_id

        # Monta query
        match_clause = f"(source:{node_type}" if node_type else "(source"
        match_clause += " {name: $name"
        if project:
            match_clause += ", project: $project"
        match_clause += "})"

        query = f"""
        MATCH {match_clause}
        OPTIONAL MATCH path = (source)<-[*1..{max_depth}]-(affected)
        WHERE affected <> source
        WITH source, affected, min(length(path)) as depth
        RETURN
            source.name as source_name,
            labels(source)[0] as source_type,
            collect(DISTINCT {{
                name: affected.name,
                type: labels(affected)[0],
                depth: depth
            }}) as affected_nodes
        """

        params = {"name": name}
        if project:
            params["project"] = project

        try:
            records = await self.conn.execute(query, params)

            if not records or records[0]["source_name"] is None:
                return ImpactResult(
                    source_name=name,
                    source_type=node_type or "Unknown",
                    error=f"Elemento não encontrado: {node_id}",
                )

            record = records[0]
            affected = []

            for node in record["affected_nodes"]:
                if node["name"]:  # Ignora nulls
                    affected.append(
                        AffectedNode(
                            name=node["name"],
                            node_type=node["type"],
                            depth=node["depth"],
                        )
                    )

            # Ordena por profundidade, depois por nome
            affected.sort(key=lambda x: (x.depth, x.name))

            return ImpactResult(
                source_name=record["source_name"],
                source_type=record["source_type"],
                affected=affected,
                max_depth=max_depth,
            )

        except Exception as e:
            logger.error(f"Erro na análise de impacto: {e}")
            return ImpactResult(
                source_name=name,
                source_type=node_type or "Unknown",
                error=str(e),
            )

    async def get_path(
        self,
        source: str,
        target: str,
        project: Optional[str] = None,
        max_paths: int = 5,
    ) -> PathResult:
        """
        Encontra caminhos entre dois nós.

        Args:
            source: Nome do nó origem
            target: Nome do nó destino
            project: Filtrar por projeto (opcional)
            max_paths: Número máximo de caminhos

        Returns:
            PathResult com caminhos encontrados
        """
        project_filter = ""
        if project:
            project_filter = "AND all(n IN nodes(path) WHERE n.project = $project)"

        query = f"""
        MATCH (a {{name: $source}})
        MATCH (b {{name: $target}})
        MATCH path = shortestPath((a)-[*]-(b))
        WHERE a <> b {project_filter}
        RETURN path
        LIMIT $max_paths
        """

        params = {
            "source": source,
            "target": target,
            "max_paths": max_paths,
        }
        if project:
            params["project"] = project

        try:
            records = await self.conn.execute(query, params)

            if not records:
                return PathResult(
                    source=source,
                    target=target,
                    error="Nenhum caminho encontrado",
                )

            paths = []
            for record in records:
                path = record["path"]
                path_nodes = []
                # path é uma lista alternada: nó, rel, nó, rel, nó...
                # Extraímos apenas os nós (índices pares)
                for i, item in enumerate(path):
                    if i % 2 == 0:  # É um nó (índice par)
                        path_nodes.append(
                            PathNode(
                                name=item.get("name", "?"),
                                node_type="Procedure",  # Por ora assumimos Procedure
                            )
                        )
                paths.append(path_nodes)

            # Ordena por tamanho
            paths.sort(key=len)

            return PathResult(source=source, target=target, paths=paths)

        except Exception as e:
            logger.error(f"Erro na busca de caminhos: {e}")
            return PathResult(source=source, target=target, error=str(e))

    async def find_hubs(
        self,
        min_connections: int = 10,
        project: Optional[str] = None,
    ) -> HubResult:
        """
        Encontra nós com muitas conexões (hubs).

        Args:
            min_connections: Mínimo de conexões para ser considerado hub
            project: Filtrar por projeto (opcional)

        Returns:
            HubResult com lista de hubs
        """
        project_filter = ""
        if project:
            project_filter = "WHERE n.project = $project"

        query = f"""
        MATCH (n)
        {project_filter}
        WITH n, COUNT {{ (n)<--() }} as incoming, COUNT {{ (n)-->() }} as outgoing
        WHERE incoming + outgoing >= $min
        RETURN
            n.name as name,
            labels(n)[0] as type,
            incoming,
            outgoing
        ORDER BY incoming + outgoing DESC
        """

        params = {"min": min_connections}
        if project:
            params["project"] = project

        try:
            records = await self.conn.execute(query, params)

            hubs = []
            for record in records:
                hubs.append(
                    HubNode(
                        name=record["name"],
                        node_type=record["type"],
                        incoming=record["incoming"],
                        outgoing=record["outgoing"],
                    )
                )

            return HubResult(min_connections=min_connections, hubs=hubs)

        except Exception as e:
            logger.error(f"Erro na busca de hubs: {e}")
            return HubResult(min_connections=min_connections, error=str(e))

    async def find_dead_code(
        self,
        project: Optional[str] = None,
        entry_point_prefixes: Optional[list[str]] = None,
    ) -> DeadCodeResult:
        """
        Encontra código potencialmente não utilizado.

        Procedures e classes sem chamadores são candidatas a código morto.
        Entry points (APIs, Tasks, UI) são excluídos.

        Args:
            project: Filtrar por projeto (opcional)
            entry_point_prefixes: Prefixos de entry points a ignorar

        Returns:
            DeadCodeResult com elementos não utilizados
        """
        if entry_point_prefixes is None:
            entry_point_prefixes = ["API", "Task", "PAGE_", "WIN_"]

        project_filter = ""
        if project:
            project_filter = "AND n.project = $project"

        # Monta filtro de prefixos
        prefix_conditions = " AND ".join(
            f"NOT n.name STARTS WITH '{p}'" for p in entry_point_prefixes
        )

        # Procedures não chamadas
        proc_query = f"""
        MATCH (n:Procedure)
        WHERE NOT ()-[:CALLS]->(n)
        {project_filter}
        AND {prefix_conditions}
        RETURN n.name as name
        ORDER BY n.name
        """

        # Classes não usadas
        class_query = f"""
        MATCH (n:Class)
        WHERE NOT ()-[:USES_CLASS]->(n)
        AND NOT ()-[:INHERITS]->(n)
        {project_filter}
        RETURN n.name as name
        ORDER BY n.name
        """

        params = {}
        if project:
            params["project"] = project

        try:
            proc_records = await self.conn.execute(proc_query, params)
            class_records = await self.conn.execute(class_query, params)

            return DeadCodeResult(
                procedures=[r["name"] for r in proc_records],
                classes=[r["name"] for r in class_records],
            )

        except Exception as e:
            logger.error(f"Erro na busca de código morto: {e}")
            return DeadCodeResult(error=str(e))

    async def find_cycles(
        self,
        node_type: str = "Procedure",
        max_length: int = 10,
        project: Optional[str] = None,
    ) -> list[list[str]]:
        """
        Encontra ciclos no grafo.

        Args:
            node_type: Tipo de nó para buscar ciclos
            max_length: Tamanho máximo do ciclo
            project: Filtrar por projeto (opcional)

        Returns:
            Lista de ciclos (cada ciclo é lista de nomes)
        """
        project_filter = ""
        if project:
            project_filter = f"AND n.project = '{project}'"

        query = f"""
        MATCH path = (n:{node_type})-[*2..{max_length}]->(n)
        WHERE true {project_filter}
        RETURN [node IN nodes(path) | node.name] as cycle
        LIMIT 100
        """

        try:
            records = await self.conn.execute(query)
            cycles = [r["cycle"] for r in records]

            # Remove duplicatas (mesmo ciclo começando de pontos diferentes)
            unique_cycles = []
            seen = set()
            for cycle in cycles:
                normalized = tuple(sorted(cycle))
                if normalized not in seen:
                    seen.add(normalized)
                    unique_cycles.append(cycle)

            return unique_cycles

        except Exception as e:
            logger.error(f"Erro na busca de ciclos: {e}")
            return []
