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
from wxcode.models.stack import Stack
from wxcode.parser.global_state_extractor import Scope


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


def _scope_to_mapping(scope: Scope) -> str:
    """
    Mapeia escopo WinDev para padrao Python recomendado.

    Args:
        scope: Escopo da variavel (APP, MODULE, REQUEST)

    Returns:
        String descrevendo padrao Python recomendado
    """
    return {
        Scope.APP: "Environment variable / Settings class",
        Scope.MODULE: "Module singleton / FastAPI Depends()",
        Scope.REQUEST: "Request context / Depends()",
    }.get(scope, "Unknown")


PROMPT_TEMPLATE = '''# Project Context for WXCODE

> **IMPORTANT: CONVERSION PROJECT**
> This is a **code conversion project**, NOT a greenfield project.
> The source code exists in a WinDev/WebDev Knowledge Base accessible via MCP tools.
> You MUST use the configured MCP server (wxcode-kb) to query original WinDev code.

## Autonomous Execution Instructions

> **EXECUTE AUTOMATICALLY - DO NOT ASK QUESTIONS**
>
> This workflow is being run headlessly. You MUST proceed without user interaction.
> Make reasonable decisions based on the context provided below.
> If something is unclear, use sensible defaults based on industry best practices.

### Phase 1: Project Initialization (DO NOW)

Execute these steps automatically:

1. **Create Project Starter**
   - Initialize the project structure for **{stack_name}**
   - Create all necessary directories per the file structure below
   - Setup configuration files (pyproject.toml, requirements.txt, .env.example, etc.)
   - Create the main application entry point

2. **Convert Database Schema**
   - Create database models for ALL {table_count} tables listed below
   - Follow the type mappings and naming conventions for {stack_name}
   - Include relationships, indexes, and constraints
   - Generate migration files if applicable

3. **Setup Project Documentation**
   - Create PROJECT.md with conversion strategy
   - Create ROADMAP.md documenting that element conversion will happen via milestones

### Phase 2: Element Conversion (VIA MILESTONES)

> **DO NOT CONVERT ELEMENTS NOW**
>
> Individual elements (pages, procedures, classes) will be converted gradually
> through separate milestone workflows. Each milestone will:
> - Receive specific element context
> - Query the Knowledge Base for source code
> - Convert that specific element
>
> This initialization phase only creates the project foundation and schema.

## What to Build

Convert a **WinDev/WebDev application** to **{stack_name}** with project name "{project_name}":

1. **Use MCP Tools**: Query the Knowledge Base to get original WinDev code before converting
2. **Database Models**: Create models based on the {table_count} tables from the original schema
3. **Convert Business Logic**: Use `get_element` and `get_procedures` to get original code
4. **Convert UI to Routes**: Use `get_controls` to understand original UI structure
5. **Preserve Functionality**: The converted code must replicate original behavior

**CRITICAL**: Before converting any element, ALWAYS:
1. Call `get_element(element_name="X", project_name="{kb_name}")` to get the source code
2. Call `get_controls(element_name="X")` to understand UI structure (for pages)
3. Call `get_dependencies(element_name="X")` to understand what it uses

This is NOT a greenfield project. Do NOT generate placeholder code - convert the REAL WinDev code.

## Project Information

- **Name:** {project_name}
- **Stack:** {stack_name}
- **Language:** {language}
- **Framework:** {framework}

## Target Stack Characteristics

### File Structure
{file_structure}

### Naming Conventions
{naming_conventions}

### Type Mappings (HyperFile -> {language})
{type_mappings}

### Model Template
```{language}
{model_template}
```

### Common Imports
```{language}
{imports_template}
```

## Database Schema ({table_count} tables)

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

{mcp_instructions}

## Execution Instructions

> **AUTONOMOUS MODE - PROCEED WITHOUT ASKING**

### DO NOW (Project Initialization):

1. **Create project structure** for {stack_name}:
   - All directories per file structure above
   - Configuration files (pyproject.toml/package.json, requirements.txt, .gitignore)
   - Main application entry point
   - Database connection setup

2. **Convert ALL database tables** ({table_count} tables):
   - Create Pydantic/SQLAlchemy models for EVERY table listed above
   - Include all columns, types, indexes, and relationships
   - Follow naming conventions for {stack_name}

3. **Create documentation**:
   - PROJECT.md: Describe the conversion project and target stack
   - ROADMAP.md: Document that element conversion will happen via milestones

### DO NOT DO NOW (Handled by Milestones):

- Converting pages (PAGE_*)
- Converting procedures (*.wdg)
- Converting classes (*.wdc)
- Converting reports (*.wde)

These will be converted one-by-one through milestone workflows that provide
specific element context and source code.

### Start Execution

Begin by creating the project structure and database models.
**Do not ask questions - make reasonable decisions and proceed.**
'''


class PromptBuilder:
    """
    Constroi arquivo CONTEXT.md para workflow GSD.

    Combina metadados de stack com schema de banco para criar
    um contexto rico que Claude Code usa para gerar codigo idiomatico.
    """

    @staticmethod
    def format_dict_as_yaml(d: dict[str, Any], indent: int = 0) -> str:
        """
        Formata dict como string YAML-like indentada.

        Args:
            d: Dicionario a formatar
            indent: Nivel de indentacao atual

        Returns:
            String formatada estilo YAML
        """
        lines = []
        prefix = "  " * indent
        for k, v in d.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(PromptBuilder.format_dict_as_yaml(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  -")
                        lines.append(PromptBuilder.format_dict_as_yaml(item, indent + 2))
                    else:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{k}: {v}")
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
            if _is_sensitive_name(var.name):
                default = "*[REDACTED]*"

            # Recommend mapping based on scope
            mapping = _scope_to_mapping(var.scope)

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
| REQUEST (Page-level) | Request context via `request.state` or `Depends()` |

### Example Conversions

**Connection globals (`gCnn is Connection`):**
- Use `DATABASE_URL` environment variable
- Configure in `app/core/config.py` as Settings field
- Inject via `Depends(get_db_session)`

**JSON parameter globals (`gjParametros is JSON`):**
- Move to Settings class if static configuration
- Use request context if per-request data

**Session/Auth globals (`gsAccessToken`, `gUsuarioLogado`):**
- Use FastAPI's built-in authentication
- Store in `request.state` after auth middleware'''

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
    # Convert HOpenConnection, Global_PegaInfoINI, etc. here
    yield
    # Shutdown: Close connections, cleanup resources
    # Convert HCloseConnection, etc. here

app = FastAPI(lifespan=lifespan)
```

**Note:** Use `@asynccontextmanager` (not deprecated `@app.on_event("startup")` / `@app.on_event("shutdown")`)

### WLanguage to FastAPI/Python Mapping

| WLanguage Pattern | FastAPI/Python Equivalent |
|-------------------|---------------------------|
| `gCnn is Connection` | `app.state.db_engine` or `Depends()` |
| `HOpenConnection(gCnn)` | `create_async_engine(DATABASE_URL)` |
| `HChangeConnection("*", gCnn)` | Default database routing in ORM |
| `COMPILE IF Configuration="X"` | Environment variables / `.env` files |
| `Global_PegaInfoINI(path, key)` | `os.getenv()` or `pydantic_settings.BaseSettings` |'''

    @staticmethod
    def format_mcp_instructions(kb_name: str) -> str:
        """
        Gera secao de instrucoes MCP para CONTEXT.md.

        Documenta ferramentas disponiveis do servidor wxcode-kb
        para consultas dinamicas durante geracao de codigo.

        Args:
            kb_name: Nome da Knowledge Base (projeto WinDev original)

        Returns:
            String markdown com instrucoes MCP
        """
        safe_kb = sanitize_identifier(kb_name)
        return f'''## MCP Server Integration

> **MANDATORY**: The `.mcp.json` file is already configured in this workspace.
> You MUST use these MCP tools to query the original WinDev code before converting.
> DO NOT generate placeholder code - get the REAL source code from the Knowledge Base.

### How to Get Source Code

**Before converting any element, ALWAYS run these MCP calls:**

```
// Step 1: Get the original WinDev source code
get_element(element_name="PAGE_Login", project_name="{safe_kb}")

// Step 2: Get UI controls and events (for pages)
get_controls(element_name="PAGE_Login", project_name="{safe_kb}")

// Step 3: Understand dependencies
get_dependencies(element_name="PAGE_Login", project_name="{safe_kb}")
```

### Available MCP Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `get_element` | Get full element with AST and code | **ALWAYS** before converting |
| `get_controls` | Get UI control hierarchy | For PAGE elements |
| `get_procedures` | List procedures with code | For procedure sets (.wdg) |
| `get_dependencies` | What this element uses/is used by | To plan conversion order |
| `search_code` | Find code patterns (regex) | To find related elements |
| `get_table` | Get table schema details | When working with data access |
| `list_elements` | List elements by type/layer | To explore what needs conversion |
| `get_conversion_candidates` | Elements ready to convert | To find next element to convert |

### Conversion Workflow

1. **Query**: `get_element(element_name="X", project_name="{safe_kb}")`
2. **Understand**: Read the WLanguage code, understand the business logic
3. **Convert**: Translate to Python/FastAPI preserving functionality
4. **Mark**: `mark_converted(element_name="X", project_name="{safe_kb}", confirm=True)`

### Knowledge Base Information

- **Project Name**: `{safe_kb}`
- **MCP Server**: `wxcode-kb` (configured in `.mcp.json`)

**REMEMBER**: This is a CONVERSION project. The original code EXISTS. Query it, don't generate from scratch.'''

    @classmethod
    def build_context(
        cls,
        output_project: OutputProject,
        stack: Stack,
        tables: list[dict],
        kb_name: str,
        connections: list = None,
        global_state: GlobalStateContext = None,
    ) -> str:
        """
        Constroi conteudo completo do CONTEXT.md.

        Args:
            output_project: Projeto de saida com nome e configuracao
            stack: Stack alvo com metadados de tecnologia
            tables: Lista de tabelas extraidas do schema
            kb_name: Nome da Knowledge Base (projeto WinDev original)
            connections: Lista de conexoes de banco (opcional)
            global_state: Contexto de variaveis globais (opcional)

        Returns:
            Conteudo formatado do CONTEXT.md
        """
        safe_kb = sanitize_identifier(kb_name)
        return PROMPT_TEMPLATE.format(
            project_name=output_project.name,
            kb_name=safe_kb,
            stack_name=stack.name,
            language=stack.language,
            framework=stack.framework,
            file_structure=cls.format_dict_as_yaml(stack.file_structure),
            naming_conventions=cls.format_dict_as_yaml(stack.naming_conventions),
            type_mappings=cls.format_dict_as_yaml(stack.type_mappings),
            model_template=stack.model_template or "# No model template defined",
            imports_template=stack.imports_template or "# No imports template defined",
            schema_tables=cls.format_tables(tables),
            table_count=len(tables),
            database_connections=cls.format_connections(connections or []),
            env_example=cls.format_env_example(connections or [], output_project.name),
            global_state_table=cls.format_global_state(global_state),
            scope_patterns=cls.format_scope_patterns() if global_state and global_state.variables else "",
            global_var_count=len(global_state.variables) if global_state else 0,
            initialization_code=cls.format_initialization_blocks(global_state),
            lifespan_pattern=cls.format_lifespan_pattern() if global_state is not None and global_state.initialization_blocks else "",
            mcp_instructions=cls.format_mcp_instructions(kb_name),
        )

    @classmethod
    def write_mcp_config(cls, workspace_path: Path) -> Path:
        """
        Escreve .mcp.json no workspace para configurar o MCP server.

        Args:
            workspace_path: Caminho do workspace do projeto

        Returns:
            Path do arquivo .mcp.json criado
        """
        # Get wxcode src path dynamically
        import wxcode
        wxcode_src = Path(wxcode.__file__).parent.parent

        mcp_config = {
            "mcpServers": {
                "wxcode-kb": {
                    "command": "python",
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
        kb_name: str,
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
            kb_name: Nome da Knowledge Base (projeto WinDev original)
            connections: Lista de conexoes de banco (opcional)
            global_state: Contexto de variaveis globais (opcional)

        Returns:
            Path do arquivo CONTEXT.md criado
        """
        # Write .mcp.json for MCP server configuration
        cls.write_mcp_config(workspace_path)

        # Write CONTEXT.md
        content = cls.build_context(
            output_project, stack, tables, kb_name=kb_name,
            connections=connections, global_state=global_state
        )
        context_path = workspace_path / "CONTEXT.md"
        context_path.write_text(content, encoding="utf-8")
        return context_path
