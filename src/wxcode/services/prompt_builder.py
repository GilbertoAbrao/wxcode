"""
Servico de construcao de prompts para workflow GSD.

Monta o arquivo CONTEXT.md com metadados de stack e schema de banco,
utilizado pelo Claude Code para converter projetos WinDev/WebDev.
"""

import json
import re
from pathlib import Path
from typing import Any

from wxcode.models.global_state_context import GlobalStateContext
from wxcode.models.output_project import OutputProject
from wxcode.models.project import Project
from wxcode.models.stack import Stack


def sanitize_identifier(name: str, max_length: int = 100) -> str:
    """
    Sanitiza identificador para inclusao segura em CONTEXT.md.

    Remove caracteres fora de [A-Za-z0-9_] para prevenir prompt injection.
    Preserva case original (diferente de workspace_manager que usa lowercase).

    Args:
        name: Nome original (elemento, tabela, conexao, variavel)
        max_length: Comprimento maximo (default 100)

    Returns:
        Nome sanitizado seguro para inclusao em prompts
    """
    if not name:
        return ""
    return re.sub(r'[^A-Za-z0-9_]', '_', name)[:max_length]


def _project_type_to_string(project_type: int) -> str:
    """
    Converte project_type numerico para string legivel.

    Args:
        project_type: Tipo numerico do projeto

    Returns:
        String descritiva do tipo
    """
    type_map = {
        4097: "WebDev",
        4098: "WinDev",
        4099: "WinDev Mobile",
    }
    return type_map.get(project_type, f"Unknown ({project_type})")


PROMPT_TEMPLATE = '''# Project Context for WXCODE

> **CONVERSION PROJECT**
> This is a code conversion project from WinDev/WebDev to modern stack.
> MCP server (wxcode-kb) provides access to the source Knowledge Base.

## Project Information

| Field | Value |
|-------|-------|
| **Name** | {project_name} |
| **Stack** | {stack_name} |
| **Stack ID** | {stack_id} |
| **Language** | {language} |
| **Framework** | {framework} |
| **ORM** | {orm} |
| **Template Engine** | {template_engine} |

## Source Project

| Field | Value |
|-------|-------|
| **Project Name** | {kb_name} |
| **Project ID** | {kb_id} |
| **Type** | {kb_type} |
| **Elements Count** | {elements_count} |
| **Tables Count** | {tables_count} |

## Output Project

| Field | Value |
|-------|-------|
| **Output ID** | {output_project_id} |
| **Workspace Path** | {workspace_path} |

## File Structure

{file_structure_table}

## Naming Conventions

{naming_conventions_table}

## Type Mappings

{type_mappings_table}

## Database Schema ({tables_count} tables)

{schema_tables}

## Database Connections

{database_connections}

## Environment Variables (.env.example)

{env_example}

## Global State ({global_var_count} variables)

{global_state_table}

{scope_patterns}

## Initialization Code

{initialization_code}

{lifespan_pattern}

## MCP Tools (25 tools)

### Elements
- `get_element` — Get WinDev source code
- `list_elements` — List all elements
- `search_code` — Search in source code

### Controls
- `get_controls` — Get UI control hierarchy
- `get_data_bindings` — Get data bindings

### Procedures
- `get_procedures` — Get global procedures
- `get_procedure` — Get specific procedure

### Schema
- `get_schema` — Get database schema
- `get_table` — Get specific table

### Graph (Neo4j)
- `get_dependencies` — Get dependencies
- `get_impact` — Get impact analysis
- `get_path` — Get path between elements
- `find_hubs` — Find critical elements
- `find_dead_code` — Find unused elements
- `find_cycles` — Find circular dependencies

### Conversion
- `get_conversion_candidates` — Get ready elements
- `get_topological_order` — Get conversion order
- `get_conversion_stats` — Get progress
- `mark_converted` — Mark as converted
- `mark_project_initialized` — Mark initialized

### Stack
- `get_stack_conventions` — Get stack conventions

### Planes
- `get_element_planes` — Detect tabs/wizard/views

### WLanguage
- `get_wlanguage_reference` — Get H* reference
- `list_wlanguage_functions` — List functions
- `get_wlanguage_pattern` — Get patterns

### Similarity
- `search_converted_similar` — Find similar converted

### PDF
- `get_element_pdf_slice` — Get PDF/screenshots
'''


class PromptBuilder:
    """
    Constroi arquivo CONTEXT.md para workflow GSD.

    Combina metadados de stack com schema de banco para criar
    um contexto rico que Claude Code usa para gerar codigo idiomatico.
    """

    @staticmethod
    def format_file_structure_table(file_structure: dict[str, str]) -> str:
        """
        Formata file_structure como tabela markdown.

        Args:
            file_structure: Dict de componente -> path

        Returns:
            String markdown formatada como tabela
        """
        if not file_structure:
            return "| Component | Path |\n|-----------|------|\n| *none* | *none* |"

        lines = ["| Component | Path |", "|-----------|------|"]
        for component, path in file_structure.items():
            lines.append(f"| {component} | {path} |")
        return "\n".join(lines)

    @staticmethod
    def format_naming_conventions_table(naming_conventions: dict[str, str]) -> str:
        """
        Formata naming_conventions como tabela markdown.

        Args:
            naming_conventions: Dict de elemento -> convenção

        Returns:
            String markdown formatada como tabela
        """
        if not naming_conventions:
            return "| Element | Convention |\n|---------|------------|\n| *none* | *none* |"

        lines = ["| Element | Convention |", "|---------|------------|"]
        for element, convention in naming_conventions.items():
            lines.append(f"| {element} | {convention} |")
        return "\n".join(lines)

    @staticmethod
    def format_type_mappings_table(type_mappings: dict[str, str]) -> str:
        """
        Formata type_mappings como tabela markdown.

        Args:
            type_mappings: Dict de tipo HyperFile -> tipo alvo

        Returns:
            String markdown formatada como tabela
        """
        if not type_mappings:
            return "| HyperFile Type | Target Type |\n|----------------|-------------|\n| *none* | *none* |"

        lines = ["| HyperFile Type | Target Type |", "|----------------|-------------|"]
        for hf_type, target_type in type_mappings.items():
            lines.append(f"| {hf_type} | {target_type} |")
        return "\n".join(lines)

    @staticmethod
    def format_tables(tables: list[dict]) -> str:
        """
        Formata tabelas como markdown com tabelas de colunas.

        Args:
            tables: Lista de dicts de tabelas com columns e indexes

        Returns:
            String markdown formatada
        """
        if not tables:
            return "*No tables found for this Configuration.*"

        lines = []
        for table in tables:
            lines.append(f"### {sanitize_identifier(table['name'])}")
            if table.get('physical_name') and table['physical_name'] != table['name']:
                lines.append(f"Physical name: `{table['physical_name']}`")
            lines.append("")
            lines.append("| Column | Type | Nullable | PK | Indexed | Auto |")
            lines.append("|--------|------|----------|----|---------| -----|")
            for col in table['columns']:
                pk = "Yes" if col.get('is_primary_key') else ""
                idx = "Yes" if col.get('is_indexed') else ""
                nullable = "Yes" if col.get('nullable') else "No"
                auto = "Yes" if col.get('is_auto_increment') else ""
                python_type = col.get('python_type', 'Any')
                lines.append(
                    f"| {col['name']} | {python_type} | {nullable} | {pk} | {idx} | {auto} |"
                )

            # Adiciona indices se houver
            if table.get('indexes'):
                lines.append("")
                lines.append("**Indexes:**")
                for idx in table['indexes']:
                    unique_marker = " (unique)" if idx.get('is_unique') else ""
                    primary_marker = " (primary)" if idx.get('is_primary') else ""
                    cols = ", ".join(idx.get('columns', []))
                    lines.append(f"- `{idx['name']}`: {cols}{unique_marker}{primary_marker}")

            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_connections(connections: list) -> str:
        """
        Formata conexoes como tabela markdown.

        Args:
            connections: Lista de SchemaConnection objects

        Returns:
            String markdown formatada
        """
        if not connections:
            return "*No external database connections defined.*"

        lines = []
        lines.append("| Connection | Host | Port | Database | Driver |")
        lines.append("|------------|------|------|----------|--------|")

        for conn in connections:
            host = getattr(conn, 'source', '') or '*local*'
            port = getattr(conn, 'port', '') or '*default*'
            database = getattr(conn, 'database', '') or '*n/a*'
            driver = getattr(conn, 'driver_name', '') or 'Unknown'
            name = sanitize_identifier(getattr(conn, 'name', 'Unknown'))

            lines.append(f"| {name} | {host} | {port} | {database} | {driver} |")

        return "\n".join(lines)

    @staticmethod
    def format_env_example(connections: list, project_name: str) -> str:
        """
        Gera conteudo .env.example para CONTEXT.md.

        Args:
            connections: Lista de SchemaConnection objects
            project_name: Nome do projeto para comentario

        Returns:
            String com bloco de codigo bash formatado
        """
        if not connections:
            return "```bash\n# No database connections - using default settings\nDATABASE_URL=\n```"

        lines = ["```bash", f"# Environment variables for {project_name}", ""]

        for conn in connections:
            conn_name = getattr(conn, 'name', 'CONNECTION')
            conn_var = conn_name.upper()
            driver = getattr(conn, 'driver_name', 'Unknown')
            port = getattr(conn, 'port', '')

            lines.append(f"# {conn_name} ({driver})")
            lines.append(f"{conn_var}_HOST=")
            lines.append(f"{conn_var}_PORT={port}")
            lines.append(f"{conn_var}_DATABASE=")
            lines.append(f"{conn_var}_USER=")
            lines.append(f"{conn_var}_PASSWORD=")
            lines.append("")

        lines.append("```")
        return "\n".join(lines)

    @staticmethod
    def _is_sensitive_name(name: str) -> bool:
        """
        Detecta nomes de variaveis potencialmente sensiveis.

        Args:
            name: Nome da variavel

        Returns:
            True se nome contem padrao sensivel
        """
        sensitive_patterns = ["token", "secret", "password", "key", "pwd", "auth", "credential"]
        name_lower = name.lower()
        return any(p in name_lower for p in sensitive_patterns)

    @staticmethod
    def _scope_to_mapping(scope) -> str:
        """
        Mapeia escopo WinDev para padrao Python recomendado.

        Args:
            scope: Escopo da variavel (APP, MODULE, REQUEST)

        Returns:
            String descrevendo padrao Python recomendado
        """
        from wxcode.parser.global_state_extractor import Scope
        return {
            Scope.APP: "Environment variable / Settings class",
            Scope.MODULE: "Module singleton / FastAPI Depends()",
            Scope.REQUEST: "Request context / Depends()",
        }.get(scope, "Unknown")

    @staticmethod
    def format_global_state(global_state: GlobalStateContext) -> str:
        """
        Formata variaveis globais como tabela markdown com anotacoes de escopo.

        Variaveis com nomes sensiveis (token, secret, etc.) tem valores
        default redatados para seguranca.

        Args:
            global_state: Contexto com variaveis globais extraidas

        Returns:
            String markdown formatada
        """
        if not global_state or not global_state.variables:
            return "*No global variables defined.*"

        lines = []
        lines.append("| Variable | Type | Default | Scope | Recommended Mapping |")
        lines.append("|----------|------|---------|-------|---------------------|")

        for var in global_state.variables:
            # Redact sensitive-looking defaults
            default = var.default_value or "*none*"
            if PromptBuilder._is_sensitive_name(var.name):
                default = "*[REDACTED]*"

            # Recommend mapping based on scope
            mapping = PromptBuilder._scope_to_mapping(var.scope)

            # Truncate long type names
            wl_type = var.wlanguage_type
            if len(wl_type) > 30:
                wl_type = wl_type[:27] + "..."

            lines.append(
                f"| `{sanitize_identifier(var.name)}` | {wl_type} | {default} | {var.scope.value} | {mapping} |"
            )

        return "\n".join(lines)

    @staticmethod
    def format_scope_patterns() -> str:
        """
        Gera documentacao de padroes de conversao para escopos globais.

        Returns:
            String markdown com padroes de conversao detalhados
        """
        return '''### Scope Conversion Patterns

| Original Scope | Recommended Python Pattern |
|----------------|---------------------------|
| APP (Project Code) | Environment variables via `pydantic.BaseSettings` |
| MODULE (Set of Procedures) | FastAPI dependency injection or module-level singleton |
| REQUEST (Page-level) | Request context via `request.state` or `Depends()` |'''

    @staticmethod
    def format_initialization_blocks(global_state: GlobalStateContext | None) -> str:
        """
        Formata blocos de inicializacao como markdown com codigo WLanguage.

        Trunca blocos maiores que 100 linhas para manter o contexto gerenciavel.

        Args:
            global_state: Contexto com blocos de inicializacao extraidos

        Returns:
            String markdown formatada com blocos de codigo
        """
        if global_state is None or not global_state.initialization_blocks:
            return "*No initialization code found.*"

        lines = []
        max_lines = 100

        for i, block in enumerate(global_state.initialization_blocks):
            lines.append(f"### Initialization Block {i + 1}")

            # Format dependencies
            deps = block.dependencies
            if deps:
                if len(deps) <= 5:
                    deps_str = ", ".join(f"`{sanitize_identifier(d)}`" for d in deps)
                else:
                    deps_str = ", ".join(f"`{sanitize_identifier(d)}`" for d in deps[:5]) + f" (+{len(deps) - 5} more)"
                lines.append(f"**References:** {deps_str}")
            else:
                lines.append("**References:** *none*")

            lines.append("")

            # Format code block with truncation
            code_lines = block.code.split("\n")
            lines.append("```wlanguage")

            if len(code_lines) > max_lines:
                lines.extend(code_lines[:max_lines])
                remaining = len(code_lines) - max_lines
                lines.append(f"// ... ({remaining} more lines)")
            else:
                lines.extend(code_lines)

            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_lifespan_pattern() -> str:
        """
        Gera documentacao do padrao lifespan do FastAPI para conversao.

        Returns:
            String markdown com padrao de conversao para lifespan
        """
        return '''### FastAPI Lifespan Pattern

The initialization code above should be converted to FastAPI's lifespan pattern:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize connections, load config
    yield
    # Shutdown: Close connections, cleanup resources

app = FastAPI(lifespan=lifespan)
```'''

    @classmethod
    def build_context(
        cls,
        output_project: OutputProject,
        stack: Stack,
        tables: list[dict],
        kb_project: Project,
        connections: list = None,
        global_state: GlobalStateContext = None,
    ) -> str:
        """
        Constroi conteudo completo do CONTEXT.md.

        Args:
            output_project: Projeto de saida com nome e configuracao
            stack: Stack alvo com metadados de tecnologia
            tables: Lista de tabelas extraidas do schema
            kb_project: Projeto Knowledge Base (WinDev original)
            connections: Lista de conexoes de banco (opcional)
            global_state: Contexto de variaveis globais (opcional)

        Returns:
            Conteudo formatado do CONTEXT.md
        """
        # Determine display name for KB
        kb_display_name = kb_project.display_name or kb_project.name

        return PROMPT_TEMPLATE.format(
            # Project Information
            project_name=output_project.name,
            stack_name=stack.name,
            stack_id=stack.stack_id,
            language=stack.language,
            framework=stack.framework,
            orm=stack.orm,
            template_engine=stack.template_engine,
            # Source Project
            kb_name=sanitize_identifier(kb_display_name),
            kb_id=str(kb_project.id),
            kb_type=_project_type_to_string(kb_project.project_type),
            elements_count=kb_project.total_elements,
            # Output Project
            output_project_id=str(output_project.id),
            workspace_path=output_project.workspace_path,
            # Tables count
            tables_count=len(tables),
            # File Structure, Naming, Type Mappings (as tables)
            file_structure_table=cls.format_file_structure_table(stack.file_structure),
            naming_conventions_table=cls.format_naming_conventions_table(stack.naming_conventions),
            type_mappings_table=cls.format_type_mappings_table(stack.type_mappings),
            # Schema
            schema_tables=cls.format_tables(tables),
            # Connections
            database_connections=cls.format_connections(connections or []),
            env_example=cls.format_env_example(connections or [], output_project.name),
            # Global State
            global_state_table=cls.format_global_state(global_state),
            scope_patterns=cls.format_scope_patterns() if global_state and global_state.variables else "",
            global_var_count=len(global_state.variables) if global_state else 0,
            initialization_code=cls.format_initialization_blocks(global_state),
            lifespan_pattern=cls.format_lifespan_pattern() if global_state is not None and global_state.initialization_blocks else "",
        )

    @classmethod
    def write_mcp_config(cls, workspace_path: Path) -> Path:
        """
        Escreve .mcp.json no workspace para configurar o MCP server (STDIO).

        Args:
            workspace_path: Caminho do workspace do projeto

        Returns:
            Path do arquivo .mcp.json criado
        """
        import wxcode

        # Get wxcode src path dynamically
        wxcode_src = Path(wxcode.__file__).parent.parent

        # Use the venv Python explicitly (not sys.executable which may be pyenv)
        # The venv is always at wxcode project root
        wxcode_root = wxcode_src.parent
        python_executable = str(wxcode_root / ".venv" / "bin" / "python")

        mcp_config = {
            "mcpServers": {
                "wxcode-kb": {
                    "command": python_executable,
                    "args": ["-m", "wxcode.mcp.server"],
                    "env": {
                        "PYTHONPATH": str(wxcode_src)
                    }
                }
            }
        }

        mcp_path = workspace_path / ".mcp.json"
        mcp_path.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
        return mcp_path

    @classmethod
    def write_context_file(
        cls,
        output_project: OutputProject,
        stack: Stack,
        tables: list[dict],
        workspace_path: Path,
        kb_project: Project,
        connections: list = None,
        global_state: GlobalStateContext = None,
    ) -> Path:
        """
        Escreve CONTEXT.md e .mcp.json no workspace e retorna o path do CONTEXT.md.

        Args:
            output_project: Projeto de saida
            stack: Stack alvo
            tables: Tabelas do schema
            workspace_path: Caminho do workspace do projeto
            kb_project: Projeto Knowledge Base (WinDev original)
            connections: Lista de conexoes de banco (opcional)
            global_state: Contexto de variaveis globais (opcional)

        Returns:
            Path do arquivo CONTEXT.md criado
        """
        # Write .mcp.json for MCP server configuration
        cls.write_mcp_config(workspace_path)

        # Write CONTEXT.md
        content = cls.build_context(
            output_project, stack, tables, kb_project=kb_project,
            connections=connections, global_state=global_state
        )
        context_path = workspace_path / "CONTEXT.md"
        context_path.write_text(content, encoding="utf-8")
        return context_path
