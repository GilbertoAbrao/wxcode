"""
Serviço para construção da árvore hierárquica do Workspace.

Constrói a árvore:
- Project (raiz)
  - Analysis
    - Tables
    - Queries
    - Connections
  - Configuration "X"
    - Pages
      - PAGE_Login
        - Proc_Validate (local)
        - Proc_OnLoad (local)
    - Procedure Groups
      - SET_Auth
        - ValidateToken
        - RefreshToken
    - Classes
      - ClassUsuario
        - Properties: Nome, Email
        - Methods: Validar()
  - Configuration "Y"
    - ...
"""

from typing import Optional

from beanie import PydanticObjectId

from wxcode.models import (
    Project,
    Element,
    ElementType,
    Procedure,
    ClassDefinition,
    DatabaseSchema,
)


# Mapeamento de tipo para ícone sugerido
TYPE_TO_ICON = {
    "project": "folder-kanban",
    "configuration": "settings",
    "analysis": "database",
    "pages": "layout",
    "procedure_groups": "file-code",
    "classes": "box",
    "queries": "search",
    "tables": "table",
    "connections": "plug",
    "page": "layout",
    "page_template": "layout-template",
    "procedure_group": "file-code",
    "browser_procedure": "globe",
    "class": "box",
    "query": "search",
    "report": "file-text",
    "rest_api": "globe",
    "webservice": "cloud",
    "procedure": "function-square",
    "method": "function-square",
    "property": "variable",
    "table": "table",
    "connection": "plug",
}

# Mapeamento de ElementType para categoria na árvore
ELEMENT_TYPE_TO_CATEGORY = {
    ElementType.PAGE: "pages",
    ElementType.PAGE_TEMPLATE: "pages",
    ElementType.PROCEDURE_GROUP: "procedure_groups",
    ElementType.BROWSER_PROCEDURE: "procedure_groups",
    ElementType.CLASS: "classes",
    ElementType.QUERY: "queries",
    ElementType.REPORT: "reports",
    ElementType.REST_API: "apis",
    ElementType.WEBSERVICE: "apis",
}

# Labels para categorias
CATEGORY_LABELS = {
    "pages": "Pages",
    "procedure_groups": "Procedure Groups",
    "classes": "Classes",
    "queries": "Queries",
    "reports": "Reports",
    "apis": "APIs",
    "tables": "Tables",
    "connections": "Connections",
}


class TreeBuilder:
    """Construtor da árvore hierárquica do Workspace."""

    async def build_project_tree(
        self,
        project_id: PydanticObjectId,
        depth: int = 1
    ) -> Optional[dict]:
        """
        Constrói a árvore do projeto até a profundidade especificada.

        Args:
            project_id: ID do projeto
            depth: Profundidade máxima (1 = só raiz, 2 = raiz + filhos, etc.)

        Returns:
            Nó raiz do projeto ou None se não encontrado.
        """
        project = await Project.get(project_id)
        if not project:
            return None

        # Nó raiz
        root = {
            "id": str(project.id),
            "name": project.name,
            "node_type": "project",
            "element_type": None,
            "status": project.status.value,
            "icon": TYPE_TO_ICON["project"],
            "has_children": True,
            "children_count": len(project.configurations) + 1,  # configs + analysis
            "children": None,
            "metadata": None,
        }

        if depth >= 2:
            children = []

            # Analysis node
            schema = await DatabaseSchema.find_one({"project_id": project.id})
            analysis_node = await self._build_analysis_node(project.id, schema, depth - 1)
            children.append(analysis_node)

            # Configuration nodes
            for config in project.configurations:
                config_node = await self._build_configuration_node(
                    project.id, config, depth - 1
                )
                children.append(config_node)

            root["children"] = children

        return root

    async def _build_analysis_node(
        self,
        project_id: PydanticObjectId,
        schema: Optional[DatabaseSchema],
        remaining_depth: int
    ) -> dict:
        """Constrói nó de Analysis com schema do banco."""
        tables_count = schema.total_tables if schema else 0
        connections_count = schema.total_connections if schema else 0

        # Contar queries do projeto
        queries_count = await Element.find({
            "project_id.$id": project_id,
            "source_type": ElementType.QUERY.value
        }).count()

        node = {
            "id": f"{project_id}:analysis",
            "name": "Analysis",
            "node_type": "analysis",
            "element_type": None,
            "status": None,
            "icon": TYPE_TO_ICON["analysis"],
            "has_children": tables_count > 0 or queries_count > 0 or connections_count > 0,
            "children_count": tables_count + queries_count + connections_count,
            "children": None,
            "metadata": None,
        }

        if remaining_depth >= 1 and node["has_children"]:
            children = []

            # Category: Tables
            if tables_count > 0:
                children.append({
                    "id": "tables",
                    "name": CATEGORY_LABELS["tables"],
                    "node_type": "category",
                    "element_type": None,
                    "status": None,
                    "icon": TYPE_TO_ICON["tables"],
                    "has_children": True,
                    "children_count": tables_count,
                    "children": None,
                    "metadata": None,
                })

            # Category: Queries
            if queries_count > 0:
                children.append({
                    "id": "queries",
                    "name": CATEGORY_LABELS["queries"],
                    "node_type": "category",
                    "element_type": None,
                    "status": None,
                    "icon": TYPE_TO_ICON["queries"],
                    "has_children": True,
                    "children_count": queries_count,
                    "children": None,
                    "metadata": None,
                })

            # Category: Connections
            if connections_count > 0:
                children.append({
                    "id": "connections",
                    "name": CATEGORY_LABELS["connections"],
                    "node_type": "category",
                    "element_type": None,
                    "status": None,
                    "icon": TYPE_TO_ICON["connections"],
                    "has_children": True,
                    "children_count": connections_count,
                    "children": None,
                    "metadata": None,
                })

            node["children"] = children

        return node

    async def _build_configuration_node(
        self,
        project_id: PydanticObjectId,
        config,
        remaining_depth: int
    ) -> dict:
        """Constrói nó de Configuration."""
        config_id = config.configuration_id

        # Contar elementos por categoria nesta configuração
        # Elemento pertence à config se config_id NOT IN excluded_from
        category_counts = {}

        for elem_type, category in ELEMENT_TYPE_TO_CATEGORY.items():
            count = await Element.find({
                "project_id.$id": project_id,
                "source_type": elem_type.value,
                "excluded_from": {"$nin": [config_id]}
            }).count()

            if count > 0:
                category_counts[category] = category_counts.get(category, 0) + count

        total_elements = sum(category_counts.values())

        node = {
            "id": config_id,
            "name": config.name,
            "node_type": "configuration",
            "element_type": None,
            "status": None,
            "icon": TYPE_TO_ICON["configuration"],
            "has_children": total_elements > 0,
            "children_count": len(category_counts),
            "children": None,
            "metadata": {
                "config_id": config_id,
            },
        }

        if remaining_depth >= 1 and total_elements > 0:
            children = []

            for category, count in sorted(category_counts.items()):
                children.append({
                    "id": f"{config_id}:{category}",
                    "name": CATEGORY_LABELS.get(category, category.title()),
                    "node_type": "category",
                    "element_type": None,
                    "status": None,
                    "icon": TYPE_TO_ICON.get(category, "folder"),
                    "has_children": True,
                    "children_count": count,
                    "children": None,
                    "metadata": {
                        "config_id": config_id,
                    },
                })

            node["children"] = children

        return node

    async def expand_configuration(
        self,
        project_id: PydanticObjectId,
        config_id: str
    ) -> list[dict]:
        """
        Expande uma configuração retornando suas categorias.

        Args:
            project_id: ID do projeto
            config_id: ID da configuração

        Returns:
            Lista de nós de categoria.
        """
        category_counts = {}

        for elem_type, category in ELEMENT_TYPE_TO_CATEGORY.items():
            count = await Element.find({
                "project_id.$id": project_id,
                "source_type": elem_type.value,
                "excluded_from": {"$nin": [config_id]}
            }).count()

            if count > 0:
                category_counts[category] = category_counts.get(category, 0) + count

        children = []
        for category, count in sorted(category_counts.items()):
            children.append({
                "id": f"{config_id}:{category}",
                "name": CATEGORY_LABELS.get(category, category.title()),
                "node_type": "category",
                "element_type": None,
                "status": None,
                "icon": TYPE_TO_ICON.get(category, "folder"),
                "has_children": True,
                "children_count": count,
                "children": None,
                "metadata": {
                    "config_id": config_id,
                },
            })

        return children

    async def expand_analysis(self, project_id: PydanticObjectId) -> list[dict]:
        """
        Expande Analysis retornando categorias (Tables, Queries, Connections).

        Args:
            project_id: ID do projeto

        Returns:
            Lista de nós de categoria.
        """
        schema = await DatabaseSchema.find_one({"project_id": project_id})

        tables_count = schema.total_tables if schema else 0
        connections_count = schema.total_connections if schema else 0

        queries_count = await Element.find({
            "project_id.$id": project_id,
            "source_type": ElementType.QUERY.value
        }).count()

        children = []

        if tables_count > 0:
            children.append({
                "id": "tables",
                "name": CATEGORY_LABELS["tables"],
                "node_type": "category",
                "element_type": None,
                "status": None,
                "icon": TYPE_TO_ICON["tables"],
                "has_children": True,
                "children_count": tables_count,
                "children": None,
                "metadata": None,
            })

        if queries_count > 0:
            children.append({
                "id": "queries",
                "name": CATEGORY_LABELS["queries"],
                "node_type": "category",
                "element_type": None,
                "status": None,
                "icon": TYPE_TO_ICON["queries"],
                "has_children": True,
                "children_count": queries_count,
                "children": None,
                "metadata": None,
            })

        if connections_count > 0:
            children.append({
                "id": "connections",
                "name": CATEGORY_LABELS["connections"],
                "node_type": "category",
                "element_type": None,
                "status": None,
                "icon": TYPE_TO_ICON["connections"],
                "has_children": True,
                "children_count": connections_count,
                "children": None,
                "metadata": None,
            })

        return children

    async def expand_category(
        self,
        project_id: PydanticObjectId,
        config_id: Optional[str],
        category: str
    ) -> list[dict]:
        """
        Expande uma categoria retornando seus elementos/itens.

        Args:
            project_id: ID do projeto
            config_id: ID da configuração (None para Analysis)
            category: Nome da categoria (pages, tables, etc.)

        Returns:
            Lista de nós de elemento.
        """
        # Categories de Analysis
        if category == "tables":
            return await self._expand_tables(project_id)
        elif category == "connections":
            return await self._expand_connections(project_id)
        elif category == "queries" and config_id is None:
            # Queries da Analysis (não de uma config específica)
            return await self._expand_queries(project_id, config_id=None)

        # Categories de Configuration
        if config_id is None:
            return []

        # Mapear categoria para ElementTypes
        category_to_types = {
            "pages": [ElementType.PAGE, ElementType.PAGE_TEMPLATE],
            "procedure_groups": [ElementType.PROCEDURE_GROUP, ElementType.BROWSER_PROCEDURE],
            "classes": [ElementType.CLASS],
            "queries": [ElementType.QUERY],
            "reports": [ElementType.REPORT],
            "apis": [ElementType.REST_API, ElementType.WEBSERVICE],
        }

        elem_types = category_to_types.get(category, [])
        if not elem_types:
            return []

        # Buscar elementos
        elements = await Element.find({
            "project_id.$id": project_id,
            "source_type": {"$in": [t.value for t in elem_types]},
            "excluded_from": {"$nin": [config_id]}
        }).sort([("source_name", 1)]).to_list()

        children = []
        for elem in elements:
            # Verificar se elemento tem procedures locais ou métodos
            has_children = False
            children_count = 0

            if elem.source_type in [ElementType.PAGE, ElementType.PAGE_TEMPLATE]:
                # Contar procedures locais
                proc_count = await Procedure.find({
                    "element_id": elem.id,
                    "is_local": True
                }).count()
                has_children = proc_count > 0
                children_count = proc_count

            elif elem.source_type == ElementType.PROCEDURE_GROUP:
                # Contar procedures do grupo
                proc_count = await Procedure.find({
                    "element_id": elem.id
                }).count()
                has_children = proc_count > 0
                children_count = proc_count

            elif elem.source_type == ElementType.CLASS:
                # Contar membros + métodos
                class_def = await ClassDefinition.find_one({"element_id": elem.id})
                if class_def:
                    children_count = len(class_def.members) + len(class_def.methods)
                    has_children = children_count > 0

            children.append({
                "id": str(elem.id),
                "name": elem.source_name,
                "node_type": "element",
                "element_type": elem.source_type.value,
                "status": elem.conversion.status.value if elem.conversion else "pending",
                "icon": TYPE_TO_ICON.get(elem.source_type.value, "file"),
                "has_children": has_children,
                "children_count": children_count,
                "children": None,
                "metadata": {
                    "element_id": str(elem.id),
                    "config_id": config_id,
                },
            })

        return children

    async def _expand_tables(self, project_id: PydanticObjectId) -> list[dict]:
        """Retorna tabelas do schema."""
        schema = await DatabaseSchema.find_one({"project_id": project_id})
        if not schema:
            return []

        children = []
        for table in sorted(schema.tables, key=lambda t: t.name):
            children.append({
                "id": f"table:{table.name}",
                "name": table.name,
                "node_type": "table",
                "element_type": None,
                "status": table.conversion_status,
                "icon": TYPE_TO_ICON["table"],
                "has_children": len(table.columns) > 0,
                "children_count": len(table.columns),
                "children": None,
                "metadata": {
                    "columns_count": len(table.columns),
                },
            })

        return children

    async def _expand_connections(self, project_id: PydanticObjectId) -> list[dict]:
        """Retorna conexões do schema."""
        schema = await DatabaseSchema.find_one({"project_id": project_id})
        if not schema:
            return []

        children = []
        for conn in sorted(schema.connections, key=lambda c: c.name):
            children.append({
                "id": f"connection:{conn.name}",
                "name": conn.name,
                "node_type": "connection",
                "element_type": None,
                "status": None,
                "icon": TYPE_TO_ICON["connection"],
                "has_children": False,
                "children_count": 0,
                "children": None,
                "metadata": None,
            })

        return children

    async def _expand_queries(
        self,
        project_id: PydanticObjectId,
        config_id: Optional[str]
    ) -> list[dict]:
        """Retorna queries do projeto/configuração."""
        query_filter = {
            "project_id.$id": project_id,
            "source_type": ElementType.QUERY.value
        }

        if config_id:
            query_filter["excluded_from"] = {"$nin": [config_id]}

        elements = await Element.find(query_filter).sort([("source_name", 1)]).to_list()

        children = []
        for elem in elements:
            children.append({
                "id": str(elem.id),
                "name": elem.source_name,
                "node_type": "query",
                "element_type": elem.source_type.value,
                "status": elem.conversion.status.value if elem.conversion else "pending",
                "icon": TYPE_TO_ICON["query"],
                "has_children": False,
                "children_count": 0,
                "children": None,
                "metadata": {
                    "element_id": str(elem.id),
                },
            })

        return children

    async def expand_element(self, element_id: PydanticObjectId) -> list[dict]:
        """
        Expande um elemento retornando seus filhos (procedures, methods, etc.).

        Args:
            element_id: ID do elemento

        Returns:
            Lista de nós filhos.
        """
        element = await Element.get(element_id)
        if not element:
            return []

        children = []

        # Pages e Page Templates: procedures locais
        if element.source_type in [ElementType.PAGE, ElementType.PAGE_TEMPLATE]:
            procedures = await Procedure.find({
                "element_id": element_id,
                "is_local": True
            }).sort([("name", 1)]).to_list()

            for proc in procedures:
                children.append({
                    "id": str(proc.id),
                    "name": proc.name,
                    "node_type": "procedure",
                    "element_type": None,
                    "status": None,
                    "icon": TYPE_TO_ICON["procedure"],
                    "has_children": False,
                    "children_count": 0,
                    "children": None,
                    "metadata": {
                        "element_id": str(element_id),
                        "parameters_count": len(proc.parameters),
                        "return_type": proc.return_type,
                        "is_local": True,
                    },
                })

        # Procedure Groups: procedures do grupo
        elif element.source_type == ElementType.PROCEDURE_GROUP:
            procedures = await Procedure.find({
                "element_id": element_id
            }).sort([("name", 1)]).to_list()

            for proc in procedures:
                children.append({
                    "id": str(proc.id),
                    "name": proc.name,
                    "node_type": "procedure",
                    "element_type": None,
                    "status": None,
                    "icon": TYPE_TO_ICON["procedure"],
                    "has_children": False,
                    "children_count": 0,
                    "children": None,
                    "metadata": {
                        "element_id": str(element_id),
                        "parameters_count": len(proc.parameters),
                        "return_type": proc.return_type,
                        "is_local": proc.is_local,
                    },
                })

        # Classes: membros + métodos
        elif element.source_type == ElementType.CLASS:
            class_def = await ClassDefinition.find_one({"element_id": element_id})
            if class_def:
                # Membros (properties)
                for member in sorted(class_def.members, key=lambda m: m.name):
                    children.append({
                        "id": f"{element_id}:member:{member.name}",
                        "name": f"{member.name}: {member.type}",
                        "node_type": "property",
                        "element_type": None,
                        "status": None,
                        "icon": TYPE_TO_ICON["property"],
                        "has_children": False,
                        "children_count": 0,
                        "children": None,
                        "metadata": {
                            "element_id": str(element_id),
                        },
                    })

                # Métodos
                for method in sorted(class_def.methods, key=lambda m: m.name):
                    children.append({
                        "id": f"{element_id}:method:{method.name}",
                        "name": method.name,
                        "node_type": "method",
                        "element_type": None,
                        "status": None,
                        "icon": TYPE_TO_ICON["method"],
                        "has_children": False,
                        "children_count": 0,
                        "children": None,
                        "metadata": {
                            "element_id": str(element_id),
                            "parameters_count": len(method.parameters),
                            "return_type": method.return_type,
                        },
                    })

        return children
