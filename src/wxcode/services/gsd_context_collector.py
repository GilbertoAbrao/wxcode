"""
GSD Context Collector - Coleta contexto completo de elementos WinDev/WebDev.

Este módulo é responsável por:
1. Coletar dados do MongoDB (element, controls, related elements)
2. Coletar análise de impacto do Neo4j
3. Gerar arquivos JSON estruturados
4. Criar CONTEXT.md otimizado para GSD workflow
5. Gerenciar branch git para o workflow
"""

import json
import secrets
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from rich.console import Console

from wxcode.graph.impact_analyzer import ImpactAnalyzer
from wxcode.graph.neo4j_connection import Neo4jConnection, Neo4jConnectionError
from wxcode.models.control import Control
from wxcode.models.control_type import ControlTypeDefinition
from wxcode.models.element import Element
from wxcode.models.procedure import Procedure
from wxcode.models.project import Project
from wxcode.models.schema import DatabaseSchema

console = Console()


@dataclass
class GSDContextData:
    """
    Agregador de todos os dados coletados para um elemento.
    """

    element: Element
    controls: list[Control]
    control_types: dict[int, ControlTypeDefinition]
    local_procedures: list[Procedure]
    dependencies: dict[str, Any]
    related_elements: list[Element]
    bound_tables: list[DatabaseSchema]
    project: Project
    stats: dict[str, Any]
    neo4j_available: bool = True


class GSDContextCollector:
    """
    Coleta contexto completo de um elemento do MongoDB e Neo4j.
    """

    def __init__(self, client: AsyncIOMotorClient, neo4j_conn: Optional[Neo4jConnection] = None):
        self.client = client
        self.neo4j_conn = neo4j_conn

    async def collect(
        self, element_name: str, project_name: Optional[str] = None, depth: int = 2
    ) -> GSDContextData:
        """
        Coleta todos os dados necessários para o contexto GSD.

        Args:
            element_name: Nome do elemento (ex: PAGE_Login)
            project_name: Nome do projeto (opcional, auto-detect se omitido)
            depth: Profundidade para análise de impacto Neo4j

        Returns:
            GSDContextData com todos os dados coletados

        Raises:
            ValueError: Se elemento não encontrado ou ambíguo
        """
        # 1. Find Element and Project
        element, project = await self._find_element(element_name, project_name)

        # 3. Fetch Controls
        controls = await self._fetch_controls(element.id)

        # 4. Fetch Local Procedures
        local_procedures = await self._fetch_local_procedures(element.id, project.id)

        # 5. Fetch Control Types
        control_types = await self._fetch_control_types(controls)

        # 5. Neo4j Impact Analysis (with fallback)
        neo4j_available = True
        dependencies = {}

        if self.neo4j_conn:
            try:
                analyzer = ImpactAnalyzer(self.neo4j_conn)
                impact = await analyzer.get_impact(element_name, depth, project.name)

                dependencies = {
                    "impact": {
                        "affected_count": impact.total_affected,
                        "by_depth": {
                            str(depth): [{"name": n.name, "type": n.node_type} for n in nodes]
                            for depth, nodes in impact.by_depth().items()
                        },
                        "by_type": {
                            node_type: [{"name": n.name, "depth": n.depth} for n in nodes]
                            for node_type, nodes in impact.by_type().items()
                        },
                        "affected_nodes": [
                            {
                                "name": node.name,
                                "type": node.node_type,
                                "depth": node.depth,
                            }
                            for node in impact.affected
                        ],
                    },
                    "uses": element.dependencies.uses if element.dependencies else [],
                    "used_by": element.dependencies.used_by if element.dependencies else [],
                    "data_files": element.dependencies.data_files if element.dependencies else [],
                    "external_apis": (
                        element.dependencies.external_apis if element.dependencies else []
                    ),
                    "bound_tables": (
                        element.dependencies.bound_tables if element.dependencies else []
                    ),
                }
            except (Neo4jConnectionError, Exception) as e:
                console.print(f"[yellow]Neo4j unavailable: {e}, using MongoDB only[/]")
                neo4j_available = False
                dependencies = self._fallback_dependencies(element)
        else:
            neo4j_available = False
            dependencies = self._fallback_dependencies(element)

        # 6. Fetch Related Elements (direct dependencies only)
        related_elements = await self._fetch_related_elements(element)

        # 7. Fetch Bound Tables
        bound_tables = await self._fetch_bound_tables(element)

        # 8. Calculate Stats
        stats = self._calculate_stats(element, controls, local_procedures)

        return GSDContextData(
            element=element,
            controls=controls,
            control_types=control_types,
            local_procedures=local_procedures,
            dependencies=dependencies,
            related_elements=related_elements,
            bound_tables=bound_tables,
            project=project,
            stats=stats,
            neo4j_available=neo4j_available,
        )

    async def _find_element(
        self, element_name: str, project_name: Optional[str]
    ) -> tuple[Element, Project]:
        """
        Encontra elemento com auto-detect de projeto se necessário.

        Returns:
            Tuple de (Element, Project)
        """
        if project_name:
            # Busca específica por projeto
            project = await Project.find_one(Project.name == project_name)
            if not project:
                raise ValueError(f"Project '{project_name}' not found")

            # Workaround: usa Motor collection diretamente para evitar problemas
            # com DBRef comparison no Beanie Link fields
            from bson import DBRef
            from wxcode.config import get_settings

            settings = get_settings()
            db = self.client[settings.mongodb_database]
            collection = db["elements"]

            # Query direto no MongoDB comparando DBRef
            project_dbref = DBRef("projects", project.id)
            elem_dict = await collection.find_one({
                "source_name": element_name,
                "project_id": project_dbref
            })

            if not elem_dict:
                raise ValueError(
                    f"Element '{element_name}' not found in project '{project_name}'"
                )

            # Carrega o elemento via Beanie usando o ID encontrado
            element = await Element.get(elem_dict["_id"])
            return element, project
        else:
            # Auto-detect: busca em todos os projetos
            elements = await Element.find(Element.source_name == element_name).to_list()

            if not elements:
                raise ValueError(f"Element '{element_name}' not found in any project")

            if len(elements) > 1:
                # Ambíguo - listar projetos
                # Usa Motor collection para evitar problemas com Link fields
                from bson import DBRef
                from wxcode.config import get_settings

                settings = get_settings()
                db = self.client[settings.mongodb_database]
                projects_coll = db["projects"]

                project_names = []
                for elem in elements:
                    # elem.project_id é um Link que armazena DBRef
                    # Precisamos extrair o ObjectId e buscar manualmente
                    if hasattr(elem, "project_id") and elem.project_id:
                        # Busca o projeto pelo ID do DBRef
                        proj_dict = await projects_coll.find_one({"_id": elem.project_id.ref.id})
                        if proj_dict:
                            project_names.append(proj_dict["name"])

                raise ValueError(
                    f"Element '{element_name}' found in multiple projects: {', '.join(project_names)}. "
                    f"Use --project to specify."
                )

            element = elements[0]
            # Carrega o projeto usando Motor collection
            from bson import DBRef
            from wxcode.config import get_settings

            settings = get_settings()
            db = self.client[settings.mongodb_database]
            proj_dict = await db["projects"].find_one({"_id": element.project_id.ref.id})
            if not proj_dict:
                raise ValueError(f"Project not found for element {element_name}")
            project = await Project.get(proj_dict["_id"])

        return element, project

    async def _fetch_controls(self, element_id: PydanticObjectId) -> list[Control]:
        """
        Busca todos os controles do elemento, ordenados por hierarquia.
        """
        # Control.element_id é ObjectId, não Link, então comparação direta funciona
        controls = await Control.find({"element_id": element_id}).sort("+full_path").to_list()
        return controls

    async def _fetch_local_procedures(
        self, element_id: PydanticObjectId, project_id: PydanticObjectId
    ) -> list[Procedure]:
        """
        Busca todas as procedures locais do elemento.

        Args:
            element_id: ID do elemento (página/window)
            project_id: ID do projeto

        Returns:
            Lista de procedures locais ordenadas por nome
        """
        procedures = await Procedure.find(
            {
                "element_id": element_id,
                "project_id": project_id,
                "is_local": True
            }
        ).sort("+name").to_list()
        return procedures

    async def _fetch_control_types(self, controls: list[Control]) -> dict[int, ControlTypeDefinition]:
        """
        Busca definições de tipos para todos os controles únicos.
        """
        # Extract unique type codes
        unique_type_codes = list(set(c.type_code for c in controls))

        # Fetch definitions
        type_defs = await ControlTypeDefinition.find(
            {"type_code": {"$in": unique_type_codes}}
        ).to_list()

        # Create dict
        return {td.type_code: td for td in type_defs}

    def _fallback_dependencies(self, element: Element) -> dict[str, Any]:
        """
        Fallback quando Neo4j não está disponível - usa apenas MongoDB.
        """
        return {
            "neo4j_unavailable": True,
            "uses": element.dependencies.uses if element.dependencies else [],
            "used_by": element.dependencies.used_by if element.dependencies else [],
            "data_files": element.dependencies.data_files if element.dependencies else [],
            "external_apis": element.dependencies.external_apis if element.dependencies else [],
            "bound_tables": element.dependencies.bound_tables if element.dependencies else [],
        }

    async def _fetch_related_elements(self, element: Element) -> list[Element]:
        """
        Busca elementos diretamente relacionados (não transitivos).
        """
        if not element.dependencies or not element.dependencies.uses:
            return []

        # Get up to 50 most important dependencies
        uses = element.dependencies.uses[:50]

        related = await Element.find({"source_name": {"$in": uses}}).to_list()
        return related

    async def _fetch_bound_tables(self, element: Element) -> list[DatabaseSchema]:
        """
        Busca tabelas vinculadas ao elemento.
        """
        if not element.dependencies or not element.dependencies.bound_tables:
            return []

        tables = await DatabaseSchema.find(
            {"table_name": {"$in": element.dependencies.bound_tables}}
        ).to_list()
        return tables

    def _calculate_stats(
        self, element: Element, controls: list[Control], local_procedures: list[Procedure]
    ) -> dict[str, Any]:
        """
        Calcula estatísticas do elemento.
        """
        return {
            "controls_total": len(controls),
            "controls_with_code": sum(1 for c in controls if c.has_code),
            "controls_with_events": sum(1 for c in controls if c.has_events),
            "controls_bound": sum(1 for c in controls if c.is_bound),
            "controls_orphan": sum(1 for c in controls if c.is_orphan),
            "max_depth": max((c.depth for c in controls), default=0),
            "local_procedures_count": len(local_procedures),
            "variables_count": len(element.ast.variables) if element.ast else 0,
            "raw_content_size": len(element.raw_content) if element.raw_content else 0,
            "needs_chunking": element.needs_chunking if hasattr(element, "needs_chunking") else False,
        }


class GSDContextWriter:
    """
    Escreve dados coletados em arquivos estruturados.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write_all(self, data: GSDContextData, branch_name: str) -> dict[str, Path]:
        """
        Escreve todos os arquivos de contexto.

        Returns:
            Dict com paths dos arquivos criados
        """
        files = {}

        # 1. element.json (com local_procedures incluídas)
        files["element"] = self._write_element(data.element, data.local_procedures)

        # 2. controls.json
        files["controls"] = self._write_controls(data.controls, data.control_types)

        # 3. dependencies.json
        files["dependencies"] = self._write_dependencies(data.dependencies)

        # 4. related-elements.json
        files["related"] = self._write_related_elements(data.related_elements)

        # 5. schema.json (if any)
        if data.bound_tables:
            files["schema"] = self._write_schema(data.bound_tables)

        # 6. neo4j-analysis.json (if available)
        if data.neo4j_available and "impact" in data.dependencies:
            files["neo4j"] = self._write_neo4j_analysis(data.dependencies)

        # 7. CONTEXT.md
        files["context"] = self._write_context_md(data, branch_name)

        console.print(f"[green]✓ Written {len(files)} files to {self.output_dir}[/]")

        return files

    def _write_element(self, element: Element, local_procedures: list[Procedure]) -> Path:
        """Escreve element.json com local_procedures incluídas"""
        path = self.output_dir / "element.json"
        data = element.model_dump(mode="json")

        # Adiciona local_procedures ao elemento
        data["local_procedures"] = [p.model_dump(mode="json") for p in local_procedures]

        self._write_json(path, data)
        return path

    def _write_controls(
        self, controls: list[Control], control_types: dict[int, ControlTypeDefinition]
    ) -> Path:
        """Escreve controls.json com tipos incluídos"""
        path = self.output_dir / "controls.json"

        # Add type definitions inline
        controls_data = []
        for control in controls:
            ctrl_dict = control.model_dump(mode="json")
            # Add type definition
            if control.type_code in control_types:
                ctrl_dict["type_definition"] = control_types[control.type_code].model_dump(
                    mode="json"
                )
            controls_data.append(ctrl_dict)

        self._write_json(path, controls_data)
        return path

    def _write_dependencies(self, dependencies: dict[str, Any]) -> Path:
        """Escreve dependencies.json"""
        path = self.output_dir / "dependencies.json"
        self._write_json(path, dependencies)
        return path

    def _write_related_elements(self, elements: list[Element]) -> Path:
        """Escreve related-elements.json"""
        path = self.output_dir / "related-elements.json"
        data = [e.model_dump(mode="json") for e in elements]
        self._write_json(path, data)
        return path

    def _write_schema(self, tables: list[DatabaseSchema]) -> Path:
        """Escreve schema.json"""
        path = self.output_dir / "schema.json"
        data = [t.model_dump(mode="json") for t in tables]
        self._write_json(path, data)
        return path

    def _write_neo4j_analysis(self, dependencies: dict[str, Any]) -> Path:
        """Escreve neo4j-analysis.json"""
        path = self.output_dir / "neo4j-analysis.json"
        self._write_json(path, dependencies.get("impact", {}))
        return path

    def _write_context_md(self, data: GSDContextData, branch_name: str) -> Path:
        """Escreve CONTEXT.md - master file para GSD"""
        path = self.output_dir / "CONTEXT.md"

        element = data.element
        stats = data.stats
        project = data.project

        # Build control hierarchy tree (top-level only)
        hierarchy_lines = []
        containers = [c for c in data.controls if c.is_container and c.depth == 0]
        for container in containers[:10]:  # Limit to 10
            child_count = sum(1 for c in data.controls if c.parent_control_id == container.id)
            # Lookup type name from control_types dictionary
            type_name = "Unknown"
            if container.type_code and container.type_code in data.control_types:
                type_name = data.control_types[container.type_code].type_name
            hierarchy_lines.append(f"- {container.name} ({type_name}) - {child_count} children")

        # Control types distribution
        type_counts: dict[str, int] = {}
        for ctrl in data.controls:
            type_code = ctrl.type_code
            if type_code in data.control_types:
                type_name = data.control_types[type_code].type_name
                type_counts[type_name] = type_counts.get(type_name, 0) + 1

        type_lines = [f"- {name}: {count}" for name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]]

        # Controls with code
        controls_with_code = [c for c in data.controls if c.has_code]
        code_lines = [f"- {c.full_path}" for c in controls_with_code[:10]]

        # Data-bound controls
        bound_controls = [c for c in data.controls if c.is_bound]
        bound_lines = [f"- {c.full_path} → {c.binding_info.get('table', 'unknown')}.{c.binding_info.get('field', 'unknown')}" if c.binding_info else f"- {c.full_path}" for c in bound_controls[:10]]

        # Dependencies summary
        uses_count = len(data.dependencies.get("uses", []))
        used_by_count = len(data.dependencies.get("used_by", []))
        uses_list = ", ".join(data.dependencies.get("uses", [])[:10])
        used_by_list = ", ".join(data.dependencies.get("used_by", [])[:10])

        # Bound tables summary
        table_lines = [
            f"- {table.table_name} ({len(table.fields)} fields)"
            for table in data.bound_tables[:5]
        ]

        # Conversion strategy
        strategy = self._generate_conversion_strategy(element)

        content = f"""# GSD Context: {element.source_name}

> **IDIOMA**: Sempre responda em **Português do Brasil (pt-BR)**.

---

## Objetivo

Você deve **converter este elemento** de WinDev/WebDev para a stack moderna:
- **Backend**: FastAPI + Pydantic
- **Templates**: Jinja2
- **Frontend**: HTMX + Alpine.js

### Importante

1. Este elemento ({element.source_name}) é **parte de um projeto maior** ({project.name})
2. Foque apenas na conversão deste elemento específico
3. Siga os padrões já existentes em `src/wxcode/generator/`
4. Gere código funcional e testável

### Entregáveis Esperados

- Rota FastAPI correspondente
- Template Jinja2 (se aplicável)
- Models Pydantic necessários
- Testes básicos (opcional)

---

**Project**: {project.name}
**Branch**: {branch_name}
**Element Type**: {element.source_type}
**Layer**: {element.layer if hasattr(element, 'layer') else 'unknown'}

---

## Quick Overview

Element: **{element.source_name}** ({element.source_type})

{self._generate_element_description(element)}

**Key Metrics**:
- Controls: {stats['controls_total']} ({stats['controls_with_code']} with code)
- Local Procedures: {stats['local_procedures_count']}
- Variables: {stats['variables_count']}
- Dependencies: {uses_count} used, {used_by_count} dependent
- Bound Tables: {len(data.bound_tables)}
- Raw Content Size: {stats['raw_content_size']:,} bytes

---

## Architecture Context

### Element Role
- **Type**: {element.source_type}
- **Layer**: {element.layer if hasattr(element, 'layer') else 'unknown'}
- **Topological Order**: {element.topological_order if hasattr(element, 'topological_order') else 'N/A'}

### Dependencies
- **Uses** ({uses_count}): {uses_list or 'None'}
- **Used By** ({used_by_count}): {used_by_list or 'None'}
- **Data Files**: {', '.join(data.dependencies.get('data_files', [])) or 'None'}
- **External APIs**: {', '.join(data.dependencies.get('external_apis', [])) or 'None'}

### Bound Tables
{''.join(table_lines) if table_lines else 'No bound tables'}

---

## UI Structure (Controls)

**Hierarchy** ({stats['controls_total']} controls, max depth {stats['max_depth']}):
{''.join(hierarchy_lines) if hierarchy_lines else 'No container controls'}

**By Type** (top 10):
{''.join(type_lines) if type_lines else 'No controls'}

**With Code** ({stats['controls_with_code']}):
{''.join(code_lines) if code_lines else 'No controls with code'}

**Data-Bound** ({stats['controls_bound']}):
{''.join(bound_lines) if bound_lines else 'No bound controls'}

---

## Local Procedures

{self._generate_procedures_section(data.local_procedures)}

---

## Conversion Goals

### Target Stack
- **Backend**: FastAPI + Pydantic
- **Templates**: Jinja2
- **Database**: PostgreSQL (Tortoise ORM)
- **Frontend**: HTMX + Alpine.js (progressive enhancement)

### Strategy
{strategy}

### Challenges
{self._identify_challenges(element, data)}

---

## Data Files Reference

| File | Description |
|------|-------------|
| element.json | Full element (AST, raw_content, metadata, dependencies, **local_procedures**) |
| controls.json | Controls (hierarchy, events, properties, bindings) |
| dependencies.json | Dependency graph (Neo4j + MongoDB) |
| related-elements.json | Direct dependencies (up to 50) |
{'| schema.json | Bound tables with fields |' if data.bound_tables else ''}
{'| neo4j-analysis.json | Impact analysis from Neo4j |' if data.neo4j_available else ''}

---

## Next Steps

1. **Review Structure**: Examine element.json and controls.json to understand component structure
2. **Analyze Dependencies**: Check dependencies.json for integration points
3. **Design Approach**: Plan conversion strategy based on element type and layer
4. **Implement Generators**: Follow existing patterns in `src/wxcode/generator/`
5. **Test Incrementally**: Validate each generated file
6. **Review Output**: Compare with original WinDev behavior

**WXCODE Workflow**: Ready for `/wxcode:new-project`

---

## Notes

- Element raw_content is included in element.json for reference
- Local procedures with full code are in element.json under `local_procedures` array
- Control hierarchy is fully resolved with parent/child relationships
- Neo4j analysis {'available' if data.neo4j_available else 'unavailable - using MongoDB fallback'}
- All ObjectIds are preserved for cross-referencing
"""

        path.write_text(content, encoding="utf-8")
        return path

    def _generate_element_description(self, element: Element) -> str:
        """Gera descrição resumida do elemento baseado no tipo."""
        descriptions = {
            "page": "WebDev page with controls, events, and business logic",
            "procedure": "Global procedure group with reusable server-side functions",
            "class": "Object-oriented class with properties and methods",
            "query": "SQL query definition for data access",
            "report": "Report template for document generation",
        }
        return descriptions.get(element.source_type.lower(), "WinDev/WebDev component")

    def _generate_procedures_section(self, procedures: list[Procedure]) -> str:
        """Gera seção de Local Procedures para o CONTEXT.md."""
        if not procedures:
            return "No local procedures defined."

        lines = [f"**Total**: {len(procedures)} local procedure(s)\n"]

        # Lista top 10 procedures com assinatura
        lines.append("**Procedures** (top 10):")
        for proc in procedures[:10]:
            # Monta assinatura
            if proc.parameters:
                params = ", ".join([
                    f"{p.name}: {p.type or 'any'}" for p in proc.parameters
                ])
                signature = f"{proc.name}({params})"
            else:
                signature = f"{proc.name}()"

            # Adiciona retorno se houver
            if proc.return_type:
                signature += f" → {proc.return_type}"

            # Conta linhas de código
            code_lines = len(proc.code.split('\n')) if proc.code else 0
            lines.append(f"- `{signature}` - {code_lines} lines")

        if len(procedures) > 10:
            lines.append(f"\n_...and {len(procedures) - 10} more procedures_")

        return "\n".join(lines)

    def _generate_conversion_strategy(self, element: Element) -> str:
        """Gera estratégia de conversão baseada no tipo."""
        strategies = {
            "page": """**PAGE → FastAPI Route + Jinja2 Template**:
- Parse controls → Generate Jinja2 template structure
- Extract procedures → Convert to FastAPI route handlers
- Map events → HTMX attributes + Alpine.js behavior
- Data bindings → ORM queries in route handlers""",
            "procedure": """**PROCEDURE_GROUP → Service Layer**:
- Extract procedures → Python functions/methods
- Convert WLanguage → Python with type hints
- Database operations → Tortoise ORM queries
- API calls → httpx async client""",
            "class": """**CLASS → Domain Model**:
- Properties → Pydantic model fields
- Methods → Class methods with type hints
- Constructor → __init__ method
- Inheritance → Python class inheritance""",
        }
        return strategies.get(element.source_type.lower(), "Custom conversion approach")

    def _identify_challenges(self, element: Element, data: GSDContextData) -> str:
        """Identifica desafios potenciais na conversão."""
        challenges = []

        if data.stats["controls_total"] > 50:
            challenges.append("- Complex UI with many controls - consider component breakdown")

        if data.stats["local_procedures_count"] > 20:
            challenges.append("- Large codebase - may need to split into multiple services")

        if data.stats["needs_chunking"]:
            challenges.append("- Large raw_content - may need streaming or pagination")

        if len(data.bound_tables) > 5:
            challenges.append("- Multiple database tables - ensure ORM relationships are correct")

        if not data.neo4j_available:
            challenges.append("- Neo4j unavailable - missing impact analysis data")

        if not challenges:
            challenges.append("- Straightforward conversion - follow standard patterns")

        return "\n".join(challenges)

    def _write_json(self, path: Path, data: Any) -> None:
        """Helper para escrever JSON com encoding correto."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=self._json_serializer)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """Custom JSON serializer para tipos não suportados."""
        if isinstance(obj, PydanticObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        # Add more types as needed
        raise TypeError(f"Type {type(obj)} not serializable")


def create_gsd_branch(element_name: str, no_branch: bool = False) -> str:
    """
    Cria branch git para o workflow GSD.

    Args:
        element_name: Nome do elemento
        no_branch: Se True, retorna branch atual sem criar nova

    Returns:
        Nome da branch criada (ou atual se no_branch=True)

    Raises:
        RuntimeError: Se operação git falhar
    """
    if no_branch:
        # Return current branch
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()

    # Sanitize element name: PAGE_Login → page-login
    sanitized = element_name.replace("_", "-").lower()

    # Random suffix: 8 hex chars
    random_suffix = secrets.token_hex(4)

    # Branch name: gsd/page-login+a1b2c3d4
    branch_name = f"gsd/{sanitized}+{random_suffix}"

    try:
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)
        console.print(f"[green]✓ Created branch: {branch_name}[/]")
        return branch_name
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to create branch: {e.stderr.decode()}")
