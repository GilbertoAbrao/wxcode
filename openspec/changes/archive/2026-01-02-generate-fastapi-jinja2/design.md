# Design: FastAPI + Jinja2 Generator

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           KNOWLEDGE BASE (MongoDB)                           │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Database │  │  Class   │  │Procedure │  │ Element  │  │ Control  │       │
│  │  Schema  │  │Definition│  │          │  │ (Pages)  │  │          │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼────────────┼─────────────┼─────────────┼──────────────┘
        │             │            │             │             │
        ▼             ▼            ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              GENERATORS                                      │
│                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Schema  │  │  Domain  │  │ Service  │  │  Route   │  │ Template │       │
│  │ Generator│  │ Generator│  │ Generator│  │ Generator│  │ Generator│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼────────────┼─────────────┼─────────────┼──────────────┘
        │             │            │             │             │
        ▼             ▼            ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT STRUCTURE                                   │
│                                                                              │
│  ./output/                                                                   │
│  ├── app/                                                                    │
│  │   ├── main.py                 # FastAPI app entry point                  │
│  │   ├── config.py               # Settings                                  │
│  │   ├── database.py             # MongoDB connection                        │
│  │   │                                                                       │
│  │   ├── models/                 # Pydantic models (from Schema)            │
│  │   │   ├── __init__.py                                                    │
│  │   │   ├── cliente.py                                                     │
│  │   │   ├── pedido.py                                                      │
│  │   │   └── ...                                                            │
│  │   │                                                                       │
│  │   ├── domain/                 # Domain classes (from ClassDefinition)    │
│  │   │   ├── __init__.py                                                    │
│  │   │   ├── class_usuario.py                                               │
│  │   │   └── ...                                                            │
│  │   │                                                                       │
│  │   ├── services/               # Business logic (from Procedures)         │
│  │   │   ├── __init__.py                                                    │
│  │   │   ├── server_procedures.py                                           │
│  │   │   ├── cliente_service.py                                             │
│  │   │   └── ...                                                            │
│  │   │                                                                       │
│  │   ├── routes/                 # FastAPI routes                           │
│  │   │   ├── __init__.py                                                    │
│  │   │   ├── clientes.py                                                    │
│  │   │   ├── pedidos.py                                                     │
│  │   │   └── ...                                                            │
│  │   │                                                                       │
│  │   └── api/                    # REST API routes (from wdrest)            │
│  │       ├── __init__.py                                                    │
│  │       └── ...                                                            │
│  │                                                                           │
│  ├── templates/                  # Jinja2 templates (from Pages)            │
│  │   ├── base.html                                                          │
│  │   ├── components/                                                        │
│  │   │   ├── navbar.html                                                    │
│  │   │   ├── sidebar.html                                                   │
│  │   │   └── ...                                                            │
│  │   ├── pages/                                                             │
│  │   │   ├── login.html                                                     │
│  │   │   ├── dashboard.html                                                 │
│  │   │   └── ...                                                            │
│  │   └── forms/                                                             │
│  │       ├── cliente_form.html                                              │
│  │       └── ...                                                            │
│  │                                                                           │
│  ├── static/                     # Static assets                            │
│  │   ├── css/                                                               │
│  │   └── js/                                                                │
│  │                                                                           │
│  ├── pyproject.toml              # Dependencies                              │
│  ├── Dockerfile                                                             │
│  └── docker-compose.yml                                                     │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Base Generator Class

```python
# src/wxcode/generator/base.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

class BaseGenerator(ABC):
    """Base class for all generators."""

    def __init__(self, project_id: str, output_dir: Path):
        self.project_id = project_id
        self.output_dir = output_dir
        self.generated_files: list[Path] = []

    @abstractmethod
    async def generate(self) -> list[Path]:
        """Generate files and return list of generated paths."""
        pass

    def write_file(self, relative_path: str, content: str) -> Path:
        """Write content to file, creating directories as needed."""
        full_path = self.output_dir / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        self.generated_files.append(full_path)
        return full_path

    def render_template(self, template_name: str, context: dict) -> str:
        """Render a Jinja2 template with context."""
        # Uses internal templates from src/wxcode/generator/templates/
        pass
```

### 2. Schema Generator

```python
# src/wxcode/generator/schema_generator.py

class SchemaGenerator(BaseGenerator):
    """Generates Pydantic models from DatabaseSchema."""

    # Mapping HyperFile types to Python types
    TYPE_MAP = {
        2: "str",           # Text
        4: "int",           # Integer
        8: "float",         # Real
        10: "datetime",     # DateTime
        11: "date",         # Date
        13: "bool",         # Boolean
        24: "int",          # AutoIncrement
        # ... etc
    }

    async def generate(self) -> list[Path]:
        schema = await DatabaseSchema.find_one({"project_id": self.project_id})

        for table in schema.tables:
            content = self._generate_model(table)
            self.write_file(f"app/models/{table.name.lower()}.py", content)

        # Generate __init__.py with exports
        self._generate_init()

        return self.generated_files

    def _generate_model(self, table: SchemaTable) -> str:
        """Generate Pydantic model for a table."""
        # Uses Jinja2 template: model.py.j2
        pass
```

### 3. Service Generator with H* Catalog

```python
# src/wxcode/generator/service_generator.py

from wxcode.transpiler.hyperfile_catalog import (
    get_hfunction,
    BufferBehavior,
    HFUNCTION_CATALOG
)

class ServiceGenerator(BaseGenerator):
    """Generates FastAPI services from Procedures."""

    async def generate(self) -> list[Path]:
        procedures = await Procedure.find(
            {"project_id": self.project_id, "is_local": False}
        ).to_list()

        # Group by element (procedure group)
        by_group = self._group_by_element(procedures)

        for group_name, procs in by_group.items():
            content = self._generate_service(group_name, procs)
            self.write_file(f"app/services/{group_name.lower()}.py", content)

        return self.generated_files

    def _convert_hfunction(self, func_name: str, args: list[str]) -> str:
        """Convert H* function to MongoDB equivalent."""
        hfunc = get_hfunction(func_name)
        if not hfunc:
            return f"# TODO: Unknown function {func_name}"

        if hfunc.needs_llm:
            return f"# TODO: Requires manual conversion - {func_name}"

        # Use mongodb_equivalent from catalog
        return self._apply_template(hfunc.mongodb_equivalent, args)
```

### 4. Template Generator

```python
# src/wxcode/generator/template_generator.py

class TemplateGenerator(BaseGenerator):
    """Generates Jinja2 templates from Pages."""

    # Control type to HTML element mapping
    CONTROL_MAP = {
        "Edit": "input",
        "Button": "button",
        "Static": "span",
        "Combo": "select",
        "Table": "table",
        "Check": "input[type=checkbox]",
        "Radio": "input[type=radio]",
        # ... etc
    }

    async def generate(self) -> list[Path]:
        # Generate base template
        self._generate_base_template()

        # Get all pages
        pages = await Element.find({
            "project_id": self.project_id,
            "source_type": "page"
        }).to_list()

        for page in pages:
            controls = await Control.find({"element_id": page.id}).to_list()
            content = self._generate_page_template(page, controls)

            page_name = page.source_name.replace("PAGE_", "").lower()
            self.write_file(f"templates/pages/{page_name}.html", content)

        return self.generated_files

    def _generate_page_template(self, page: Element, controls: list[Control]) -> str:
        """Generate Jinja2 template for a page."""
        # Detect page type: form, list, dashboard
        page_type = self._detect_page_type(controls)

        # Use appropriate template
        if page_type == "form":
            return self._generate_form_template(page, controls)
        elif page_type == "list":
            return self._generate_list_template(page, controls)
        else:
            return self._generate_generic_template(page, controls)
```

### 5. Generator Orchestrator

```python
# src/wxcode/generator/orchestrator.py

class GeneratorOrchestrator:
    """Orchestrates all generators in correct order."""

    def __init__(self, project_id: str, output_dir: Path):
        self.project_id = project_id
        self.output_dir = output_dir

        # Generators in dependency order
        self.generators = [
            SchemaGenerator(project_id, output_dir),
            DomainGenerator(project_id, output_dir),
            ServiceGenerator(project_id, output_dir),
            RouteGenerator(project_id, output_dir),
            TemplateGenerator(project_id, output_dir),
        ]

    async def generate_all(self) -> GenerationResult:
        """Run all generators and return result."""
        result = GenerationResult()

        for generator in self.generators:
            try:
                files = await generator.generate()
                result.add_success(generator.__class__.__name__, files)
            except Exception as e:
                result.add_error(generator.__class__.__name__, str(e))

        # Generate boilerplate
        self._generate_main_py()
        self._generate_config()
        self._generate_docker_files()
        self._generate_pyproject_toml()

        return result
```

## CLI Integration

```python
# src/wxcode/cli.py

@app.command()
def generate(
    project_name: str = typer.Argument(..., help="Nome do projeto"),
    output: Path = typer.Option("./output", help="Diretório de saída"),
    layers: list[str] = typer.Option(
        None,
        "--layer", "-l",
        help="Camadas específicas (schema, domain, service, route, template)"
    ),
):
    """Gera código FastAPI + Jinja2 a partir da Knowledge Base."""

    async def _generate():
        project = await Project.find_one({"name": project_name})
        if not project:
            console.print(f"[red]Projeto '{project_name}' não encontrado[/red]")
            raise typer.Exit(1)

        orchestrator = GeneratorOrchestrator(str(project.id), output)

        if layers:
            result = await orchestrator.generate_layers(layers)
        else:
            result = await orchestrator.generate_all()

        # Print summary
        console.print(f"\n[green]Geração concluída![/green]")
        console.print(f"  Arquivos gerados: {result.total_files}")
        console.print(f"  Diretório: {output}")

        if result.errors:
            console.print(f"\n[yellow]Avisos:[/yellow]")
            for error in result.errors:
                console.print(f"  - {error}")

    asyncio.run(_generate())
```

## Template Files Structure

```
src/wxcode/generator/templates/
├── python/
│   ├── model.py.j2           # Pydantic model template
│   ├── service.py.j2         # Service class template
│   ├── route.py.j2           # FastAPI route template
│   ├── domain_class.py.j2    # Domain class template
│   ├── main.py.j2            # FastAPI app entry
│   └── config.py.j2          # Settings template
│
├── jinja2/
│   ├── base.html.j2          # Base HTML template
│   ├── form.html.j2          # Form page template
│   ├── list.html.j2          # List/table page template
│   ├── dashboard.html.j2     # Dashboard template
│   └── components/
│       ├── navbar.html.j2
│       ├── sidebar.html.j2
│       ├── table.html.j2
│       └── form_field.html.j2
│
└── deploy/
    ├── Dockerfile.j2
    ├── docker-compose.yml.j2
    └── pyproject.toml.j2
```

## Type Conversion Strategy

### HyperFile → Python Types

| HyperFile Code | HyperFile Type | Python Type | Pydantic Type |
|----------------|----------------|-------------|---------------|
| 2 | Text | str | str |
| 4 | Integer | int | int |
| 8 | Real | float | float |
| 10 | DateTime | datetime | datetime |
| 11 | Date | date | date |
| 12 | Time | time | time |
| 13 | Boolean | bool | bool |
| 14 | Currency | Decimal | condecimal |
| 16 | Memo | str | str |
| 24 | AutoID | int | int |
| 26 | UUID | UUID | UUID |

### WLanguage → Python Control Flow

| WLanguage | Python |
|-----------|--------|
| `IF...THEN...ELSE...END` | `if...elif...else:` |
| `SWITCH x...CASE...END` | `match x:...case:` |
| `FOR i = 1 TO n` | `for i in range(1, n+1):` |
| `FOR EACH x OF array` | `for x in array:` |
| `WHILE...END` | `while ...:` |
| `LOOP...END` | `while True:...break` |
| `RESULT x` | `return x` |
| `RETURN` | `return` |

### H* Functions → MongoDB (via catalog)

| H* Function | MongoDB Equivalent |
|-------------|-------------------|
| `HReadSeekFirst(T, K, V)` | `db.T.find_one({K: V})` |
| `HReadFirst(T)` | `db.T.find().limit(1)` |
| `HReadNext(T)` | `for doc in cursor:` |
| `HAdd(T)` | `db.T.insert_one(doc)` |
| `HModify(T)` | `db.T.update_one({...})` |
| `HDelete(T)` | `db.T.delete_one({...})` |
| `HNbRec(T)` | `db.T.count_documents({})` |

## Error Handling

### Conversion Markers

When code cannot be automatically converted:

```python
# In generated service:

async def complex_procedure(self, param1: str) -> dict:
    # TODO: [WXCODE] Manual conversion required
    # Original WLanguage:
    # ```wlanguage
    # HExecuteQuery(QRY_COMPLEX, hQueryDefault, param1)
    # WHILE NOT HOut(QRY_COMPLEX)
    #     ...complex logic...
    #     HReadNext(QRY_COMPLEX)
    # END
    # ```
    # Reason: HExecuteQuery requires SQL analysis
    raise NotImplementedError("Requires manual conversion")
```

### Validation Markers

```python
# In generated model:

class Cliente(BaseModel):
    id: int
    nome: str
    cpf: str  # TODO: [WXCODE] Add CPF validator
    email: str  # TODO: [WXCODE] Add email validator
```

## Performance Considerations

1. **Batch Processing**: Generate files in batches to avoid memory issues
2. **Async I/O**: Use aiofiles for file writing
3. **Caching**: Cache loaded templates
4. **Progress Tracking**: Use Rich progress bar for large projects

## Testing Strategy

1. **Unit Tests**: Each generator has isolated tests
2. **Integration Tests**: Full generation with test project
3. **Snapshot Tests**: Compare generated output with expected
4. **Syntax Validation**: Run `python -m py_compile` on generated Python
5. **Template Validation**: Render templates with Jinja2 to check syntax
