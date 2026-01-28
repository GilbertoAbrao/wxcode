"""
Serviço de sincronização MongoDB -> Neo4j.
"""

from dataclasses import dataclass, field
from typing import Optional
import logging

from bson import ObjectId
from beanie.operators import In

from wxcode.graph.neo4j_connection import Neo4jConnection
from wxcode.models import (
    Project,
    Element,
    ElementType,
    DatabaseSchema,
    ClassDefinition,
    Procedure,
)

logger = logging.getLogger(__name__)


def _project_id_filter(project_id: ObjectId) -> dict:
    """
    Cria filtro MongoDB para project_id que é um Link/DBRef.

    O project_id em Element é um Link (DBRef), então precisamos
    usar a sintaxe correta para comparar.
    """
    return {"project_id.$id": project_id}


@dataclass
class SyncResult:
    """Resultado da sincronização."""

    project_name: str
    nodes_created: int = 0
    relationships_created: int = 0
    tables_count: int = 0
    classes_count: int = 0
    procedures_count: int = 0
    pages_count: int = 0
    windows_count: int = 0
    queries_count: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """True se sincronização foi bem sucedida."""
        return len(self.errors) == 0

    def __str__(self) -> str:
        return (
            f"SyncResult({self.project_name}): "
            f"{self.nodes_created} nós, "
            f"{self.relationships_created} relacionamentos"
        )


class Neo4jSyncService:
    """
    Sincroniza grafo de dependências do MongoDB para Neo4j.

    MongoDB permanece como source of truth.
    Neo4j é sincronizado on-demand para análise avançada.
    """

    def __init__(self, connection: Neo4jConnection):
        """
        Inicializa o serviço.

        Args:
            connection: Conexão Neo4j estabelecida
        """
        self.conn = connection

    async def sync_project(
        self,
        project_id: ObjectId,
        clear: bool = True,
        validate: bool = True,
    ) -> SyncResult:
        """
        Sincroniza projeto completo do MongoDB para Neo4j.

        Args:
            project_id: ID do projeto no MongoDB
            clear: Limpa dados existentes antes de sincronizar
            validate: Valida contagens após sync

        Returns:
            SyncResult com estatísticas da sincronização
        """
        # Busca projeto
        project = await Project.get(project_id)
        if not project:
            raise ValueError(f"Projeto não encontrado: {project_id}")

        result = SyncResult(project_name=project.name)
        logger.info(f"Iniciando sync do projeto {project.name}")

        try:
            # 1. Limpa dados existentes se solicitado
            if clear:
                await self.conn.clear_project(project.name)

            # 2. Cria indexes
            await self.conn.create_indexes()

            # 3. Sincroniza cada tipo de entidade
            result.tables_count = await self._sync_tables(project_id, project.name)
            result.nodes_created += result.tables_count

            result.classes_count = await self._sync_classes(project_id, project.name)
            result.nodes_created += result.classes_count

            result.procedures_count = await self._sync_procedures(
                project_id, project.name
            )
            result.nodes_created += result.procedures_count

            pages, windows, queries = await self._sync_elements(
                project_id, project.name
            )
            result.pages_count = pages
            result.windows_count = windows
            result.queries_count = queries
            result.nodes_created += pages + windows + queries

            # 4. Cria relacionamentos
            rels = await self._create_relationships(project_id, project.name)
            result.relationships_created = rels

            # 5. Valida se solicitado
            if validate:
                await self._validate_sync(result)

            logger.info(f"Sync completo: {result}")

        except Exception as e:
            result.errors.append(str(e))
            logger.error(f"Erro no sync: {e}")

        return result

    async def _sync_tables(self, project_id: ObjectId, project_name: str) -> int:
        """Sincroniza tabelas do schema."""
        schema = await DatabaseSchema.find_one(
            DatabaseSchema.project_id == project_id
        )
        if not schema:
            logger.warning(f"Schema não encontrado para projeto {project_id}")
            return 0

        nodes = []
        for table in schema.tables:
            nodes.append(
                {
                    "name": table.name,
                    "project": project_name,
                    "layer": "schema",
                    "physical_name": table.physical_name,
                    "connection": table.connection_name,
                    "column_count": len(table.columns),
                }
            )

        if not nodes:
            return 0

        query = """
        UNWIND $items as item
        CREATE (n:Table {
            name: item.name,
            project: item.project,
            layer: item.layer,
            physical_name: item.physical_name,
            connection: item.connection,
            column_count: item.column_count
        })
        """
        count = await self.conn.batch_create(nodes, query)
        logger.info(f"Sincronizadas {len(nodes)} tabelas")
        return len(nodes)

    async def _sync_classes(self, project_id: ObjectId, project_name: str) -> int:
        """Sincroniza classes."""
        classes = await ClassDefinition.find(
            ClassDefinition.project_id == project_id
        ).to_list()

        nodes = []
        for cls in classes:
            nodes.append(
                {
                    "name": cls.name,
                    "project": project_name,
                    "layer": "domain",
                    "mongo_id": str(cls.id),
                    "inherits_from": cls.inherits_from,
                    "is_abstract": cls.is_abstract,
                    "member_count": len(cls.members),
                    "method_count": len(cls.methods),
                }
            )

        if not nodes:
            return 0

        query = """
        UNWIND $items as item
        CREATE (n:Class {
            name: item.name,
            project: item.project,
            layer: item.layer,
            mongo_id: item.mongo_id,
            inherits_from: item.inherits_from,
            is_abstract: item.is_abstract,
            member_count: item.member_count,
            method_count: item.method_count
        })
        """
        await self.conn.batch_create(nodes, query)
        logger.info(f"Sincronizadas {len(nodes)} classes")
        return len(nodes)

    async def _sync_procedures(self, project_id: ObjectId, project_name: str) -> int:
        """Sincroniza procedures."""
        procedures = await Procedure.find(
            Procedure.project_id == project_id
        ).to_list()

        # Pré-carrega elementos para qualificar nomes de procedures locais
        elements_by_id: dict[str, str] = {}
        has_local_procs = any(p.is_local and p.element_id for p in procedures)
        if has_local_procs:
            elements = await Element.find(
                _project_id_filter(project_id)
            ).to_list()
            elements_by_id = {str(e.id): e.source_name for e in elements}

        nodes = []
        for proc in procedures:
            # Qualifica nome de procedures locais: PAGE_Login.MyPage
            proc_name = proc.name
            if proc.is_local and proc.element_id:
                parent_name = elements_by_id.get(str(proc.element_id))
                if parent_name:
                    proc_name = f"{parent_name}.{proc.name}"

            nodes.append(
                {
                    "name": proc_name,
                    "project": project_name,
                    "layer": "business",
                    "mongo_id": str(proc.id),
                    "is_public": proc.is_public,
                    "is_local": proc.is_local,
                    "scope": proc.scope,
                    "code_lines": proc.code_lines,
                    "param_count": len(proc.parameters),
                }
            )

        if not nodes:
            return 0

        query = """
        UNWIND $items as item
        CREATE (n:Procedure {
            name: item.name,
            project: item.project,
            layer: item.layer,
            mongo_id: item.mongo_id,
            is_public: item.is_public,
            is_local: item.is_local,
            scope: item.scope,
            code_lines: item.code_lines,
            param_count: item.param_count
        })
        """
        await self.conn.batch_create(nodes, query)
        logger.info(f"Sincronizadas {len(nodes)} procedures")
        return len(nodes)

    async def _sync_elements(
        self, project_id: ObjectId, project_name: str
    ) -> tuple[int, int, int]:
        """Sincroniza elementos (pages, windows, queries)."""
        elements = await Element.find(
            _project_id_filter(project_id),
            {"source_type": {"$in": [ElementType.PAGE.value, ElementType.WINDOW.value, ElementType.QUERY.value]}},
        ).to_list()

        pages = []
        windows = []
        queries = []

        for elem in elements:
            node = {
                "name": elem.source_name,
                "project": project_name,
                "layer": elem.layer.value if elem.layer else "ui",
                "mongo_id": str(elem.id),
                "topological_order": elem.topological_order,
            }

            if elem.source_type == ElementType.PAGE:
                pages.append(node)
            elif elem.source_type == ElementType.WINDOW:
                windows.append(node)
            elif elem.source_type == ElementType.QUERY:
                queries.append(node)

        # Criar nós por tipo
        if pages:
            query = """
            UNWIND $items as item
            CREATE (n:Page {
                name: item.name,
                project: item.project,
                layer: item.layer,
                mongo_id: item.mongo_id,
                topological_order: item.topological_order
            })
            """
            await self.conn.batch_create(pages, query)
            logger.info(f"Sincronizadas {len(pages)} páginas")

        if windows:
            query = """
            UNWIND $items as item
            CREATE (n:Window {
                name: item.name,
                project: item.project,
                layer: item.layer,
                mongo_id: item.mongo_id,
                topological_order: item.topological_order
            })
            """
            await self.conn.batch_create(windows, query)
            logger.info(f"Sincronizadas {len(windows)} windows")

        if queries:
            query = """
            UNWIND $items as item
            CREATE (n:Query {
                name: item.name,
                project: item.project,
                layer: item.layer,
                mongo_id: item.mongo_id,
                topological_order: item.topological_order
            })
            """
            await self.conn.batch_create(queries, query)
            logger.info(f"Sincronizadas {len(queries)} queries")

        return len(pages), len(windows), len(queries)

    async def _create_relationships(
        self, project_id: ObjectId, project_name: str
    ) -> int:
        """Cria todos os relacionamentos."""
        total = 0

        # 1. :INHERITS (Class -> Class)
        total += await self._create_inheritance_rels(project_name)

        # 2. :USES_TABLE (de todas as entidades)
        total += await self._create_uses_table_rels(project_name)

        # 3. :CALLS (Procedure -> Procedure)
        total += await self._create_calls_rels(project_id, project_name)

        # 4. :CALLS (Page/Window -> Procedure)
        total += await self._create_element_calls_rels(project_id, project_name)

        # 5. :USES_CLASS (Procedure, Page -> Class)
        total += await self._create_uses_class_rels(project_name)

        return total

    async def _create_inheritance_rels(self, project_name: str) -> int:
        """Cria relacionamentos de herança entre classes."""
        query = """
        MATCH (child:Class {project: $project})
        WHERE child.inherits_from IS NOT NULL
        MATCH (parent:Class {project: $project, name: child.inherits_from})
        CREATE (child)-[:INHERITS]->(parent)
        RETURN count(*) as count
        """
        result = await self.conn.execute(query, {"project": project_name})
        count = result[0]["count"] if result else 0
        logger.info(f"Criados {count} relacionamentos :INHERITS")
        return count

    async def _create_uses_table_rels(self, project_name: str) -> int:
        """Cria relacionamentos :USES_TABLE."""
        # De classes
        classes = await ClassDefinition.find().to_list()
        class_rels = []
        for cls in classes:
            for table in cls.dependencies.uses_files:
                class_rels.append({"from_name": cls.name, "to_name": table})

        # De procedures
        procedures = await Procedure.find().to_list()
        proc_rels = []
        for proc in procedures:
            for table in proc.dependencies.uses_files:
                proc_rels.append({"from_name": proc.name, "to_name": table})

        # De elementos (pages, windows)
        elements = await Element.find(
            {"source_type": {"$in": [ElementType.PAGE.value, ElementType.WINDOW.value]}}
        ).to_list()
        elem_rels = []
        for elem in elements:
            for table in elem.dependencies.data_files:
                elem_rels.append({"from_name": elem.source_name, "to_name": table})
            for table in elem.dependencies.bound_tables:
                elem_rels.append({"from_name": elem.source_name, "to_name": table})

        total = 0

        # Criar relacionamentos de classes
        if class_rels:
            query = """
            UNWIND $items as item
            MATCH (c:Class {project: $project, name: item.from_name})
            MATCH (t:Table {project: $project, name: item.to_name})
            MERGE (c)-[:USES_TABLE]->(t)
            RETURN count(*) as count
            """
            result = await self.conn.execute(
                query, {"items": class_rels, "project": project_name}
            )
            total += result[0]["count"] if result else 0

        # Criar relacionamentos de procedures
        if proc_rels:
            query = """
            UNWIND $items as item
            MATCH (p:Procedure {project: $project, name: item.from_name})
            MATCH (t:Table {project: $project, name: item.to_name})
            MERGE (p)-[:USES_TABLE]->(t)
            RETURN count(*) as count
            """
            result = await self.conn.execute(
                query, {"items": proc_rels, "project": project_name}
            )
            total += result[0]["count"] if result else 0

        # Criar relacionamentos de elementos
        if elem_rels:
            query = """
            UNWIND $items as item
            MATCH (e {project: $project, name: item.from_name})
            WHERE e:Page OR e:Window
            MATCH (t:Table {project: $project, name: item.to_name})
            MERGE (e)-[:USES_TABLE]->(t)
            RETURN count(*) as count
            """
            result = await self.conn.execute(
                query, {"items": elem_rels, "project": project_name}
            )
            total += result[0]["count"] if result else 0

        logger.info(f"Criados {total} relacionamentos :USES_TABLE")
        return total

    async def _create_calls_rels(
        self, project_id: ObjectId, project_name: str
    ) -> int:
        """Cria relacionamentos :CALLS entre procedures."""
        procedures = await Procedure.find(
            Procedure.project_id == project_id
        ).to_list()

        # Pré-carrega elementos para qualificar nomes de procedures locais
        elements_by_id: dict[str, str] = {}
        has_local_procs = any(p.is_local and p.element_id for p in procedures)
        if has_local_procs:
            elements = await Element.find(
                _project_id_filter(project_id)
            ).to_list()
            elements_by_id = {str(e.id): e.source_name for e in elements}

        # Mapa de nome original -> nome qualificado
        qualified_names: dict[str, str] = {}
        for proc in procedures:
            proc_name = proc.name
            if proc.is_local and proc.element_id:
                parent_name = elements_by_id.get(str(proc.element_id))
                if parent_name:
                    proc_name = f"{parent_name}.{proc.name}"
            qualified_names[proc.name] = proc_name

        rels = []
        for proc in procedures:
            from_name = qualified_names.get(proc.name, proc.name)
            for called in proc.dependencies.calls_procedures:
                # Se called está no mapa, usa nome qualificado; senão usa original
                to_name = qualified_names.get(called, called)
                rels.append({"from_name": from_name, "to_name": to_name})

        if not rels:
            return 0

        query = """
        UNWIND $items as item
        MATCH (caller:Procedure {project: $project, name: item.from_name})
        MATCH (callee:Procedure {project: $project, name: item.to_name})
        MERGE (caller)-[:CALLS]->(callee)
        RETURN count(*) as count
        """
        result = await self.conn.execute(
            query, {"items": rels, "project": project_name}
        )
        count = result[0]["count"] if result else 0
        logger.info(f"Criados {count} relacionamentos :CALLS")
        return count

    async def _create_element_calls_rels(
        self, project_id: ObjectId, project_name: str
    ) -> int:
        """Cria relacionamentos :CALLS de Pages/Windows para Procedures."""
        # Busca elements (Pages e Windows)
        elements = await Element.find(
            _project_id_filter(project_id),
            {"source_type": {"$in": [ElementType.PAGE.value, ElementType.WINDOW.value]}},
        ).to_list()

        # Busca todas procedures locais para criar mapa por elemento
        local_procedures = await Procedure.find(
            Procedure.project_id == project_id,
            Procedure.is_local == True
        ).to_list()

        # Mapa: element_id -> {proc_name -> qualified_name}
        local_procs_by_element: dict[str, dict[str, str]] = {}
        for proc in local_procedures:
            if proc.element_id:
                elem_id = str(proc.element_id)
                if elem_id not in local_procs_by_element:
                    local_procs_by_element[elem_id] = {}
                # Carrega nome qualificado apenas se ainda não foi feito
                if proc.name not in local_procs_by_element[elem_id]:
                    elem = await Element.get(proc.element_id)
                    if elem:
                        qualified_name = f"{elem.source_name}.{proc.name}"
                        local_procs_by_element[elem_id][proc.name] = qualified_name

        rels = []
        for elem in elements:
            if not elem.dependencies or not elem.dependencies.uses:
                continue

            from_name = elem.source_name
            elem_id = str(elem.id)

            # Mapa de procedures locais DESTE elemento
            elem_local_procs = local_procs_by_element.get(elem_id, {})

            for called in elem.dependencies.uses:
                # Se é procedure local deste elemento, usa nome qualificado
                # Senão, usa nome original (pode ser global ou local de outro elemento)
                to_name = elem_local_procs.get(called, called)
                rels.append({"from_name": from_name, "to_name": to_name})

        if not rels:
            logger.info("Nenhum relacionamento :CALLS de Pages/Windows para Procedures")
            return 0

        # Cria relacionamentos Page -> Procedure
        query_page = """
        UNWIND $items as item
        MATCH (page:Page {project: $project, name: item.from_name})
        MATCH (proc:Procedure {project: $project, name: item.to_name})
        MERGE (page)-[:CALLS]->(proc)
        RETURN count(*) as count
        """
        result_page = await self.conn.execute(
            query_page, {"items": rels, "project": project_name}
        )
        count_page = result_page[0]["count"] if result_page else 0

        # Cria relacionamentos Window -> Procedure
        query_window = """
        UNWIND $items as item
        MATCH (window:Window {project: $project, name: item.from_name})
        MATCH (proc:Procedure {project: $project, name: item.to_name})
        MERGE (window)-[:CALLS]->(proc)
        RETURN count(*) as count
        """
        result_window = await self.conn.execute(
            query_window, {"items": rels, "project": project_name}
        )
        count_window = result_window[0]["count"] if result_window else 0

        total = count_page + count_window
        logger.info(f"Criados {total} relacionamentos :CALLS de Pages/Windows para Procedures")
        return total

    async def _create_uses_class_rels(self, project_name: str) -> int:
        """Cria relacionamentos :USES_CLASS."""
        # De procedures
        procedures = await Procedure.find().to_list()
        proc_rels = []
        # Nota: precisaríamos extrair dependências de classes das procedures
        # Por ora, deixamos vazio

        # De classes (composição)
        classes = await ClassDefinition.find().to_list()
        class_rels = []
        for cls in classes:
            for used_class in cls.dependencies.uses_classes:
                if used_class != cls.inherits_from:  # Já temos INHERITS
                    class_rels.append({"from_name": cls.name, "to_name": used_class})

        total = 0

        if class_rels:
            query = """
            UNWIND $items as item
            MATCH (c1:Class {project: $project, name: item.from_name})
            MATCH (c2:Class {project: $project, name: item.to_name})
            MERGE (c1)-[:USES_CLASS]->(c2)
            RETURN count(*) as count
            """
            result = await self.conn.execute(
                query, {"items": class_rels, "project": project_name}
            )
            total += result[0]["count"] if result else 0

        logger.info(f"Criados {total} relacionamentos :USES_CLASS")
        return total

    async def _validate_sync(self, result: SyncResult) -> None:
        """Valida a sincronização comparando contagens."""
        stats = await self.conn.get_stats()
        logger.info(f"Estatísticas Neo4j: {stats}")

        # Valida contagens básicas
        expected_nodes = (
            result.tables_count
            + result.classes_count
            + result.procedures_count
            + result.pages_count
            + result.windows_count
            + result.queries_count
        )

        total_neo4j = sum(stats.values())

        if total_neo4j < expected_nodes:
            result.errors.append(
                f"Nós criados ({total_neo4j}) menor que esperado ({expected_nodes})"
            )

    async def dry_run(self, project_id: ObjectId) -> SyncResult:
        """
        Executa dry-run sem modificar Neo4j.

        Retorna estatísticas de o que seria sincronizado.
        """
        project = await Project.get(project_id)
        if not project:
            raise ValueError(f"Projeto não encontrado: {project_id}")

        result = SyncResult(project_name=project.name)

        # Conta tabelas
        schema = await DatabaseSchema.find_one(
            DatabaseSchema.project_id == project_id
        )
        if schema:
            result.tables_count = len(schema.tables)

        # Conta classes
        result.classes_count = await ClassDefinition.find(
            ClassDefinition.project_id == project_id
        ).count()

        # Conta procedures
        result.procedures_count = await Procedure.find(
            Procedure.project_id == project_id
        ).count()

        # Conta elementos
        elements = await Element.find(
            _project_id_filter(project_id),
            {"source_type": {"$in": [ElementType.PAGE.value, ElementType.WINDOW.value, ElementType.QUERY.value]}},
        ).to_list()

        for elem in elements:
            if elem.source_type == ElementType.PAGE:
                result.pages_count += 1
            elif elem.source_type == ElementType.WINDOW:
                result.windows_count += 1
            elif elem.source_type == ElementType.QUERY:
                result.queries_count += 1

        result.nodes_created = (
            result.tables_count
            + result.classes_count
            + result.procedures_count
            + result.pages_count
            + result.windows_count
            + result.queries_count
        )

        return result
