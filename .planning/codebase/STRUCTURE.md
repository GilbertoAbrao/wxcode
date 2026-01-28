# Codebase Structure

**Analysis Date:** 2026-01-21

## Directory Layout

```
wxcode/
├── .claude/                      # Claude Code integration
│   ├── commands/                # Custom commands
│   └── skills/                  # Reusable skill modules
├── .planning/                   # GSD planning docs
│   └── codebase/               # Architecture analyses
├── docs/                        # Project documentation
│   ├── VISION.md               # Strategic vision
│   ├── MASTER-PLAN.md          # Phased roadmap
│   ├── architecture.md         # Architecture diagrams
│   ├── wlanguage/              # WLanguage reference
│   └── adr/                    # Architectural Decision Records
├── openspec/                   # Specification and change management
│   ├── project.md              # Technical context
│   ├── AGENTS.md               # AI agent instructions
│   ├── specs/                  # Authoritative specs
│   ├── changes/                # In-progress changes
│   └── archive/                # Completed changes
├── src/wxcode/              # Main application source (36.5k LOC)
│   ├── __init__.py             # Package metadata
│   ├── main.py                 # FastAPI application entry point
│   ├── cli.py                  # Typer CLI entry point (162k)
│   ├── config.py               # Settings from environment
│   ├── database.py             # MongoDB/Beanie initialization
│   ├── preview_server.py       # Preview server for generated code
│   ├── parser/                 # WinDev file extraction (6.5k LOC)
│   │   ├── project_mapper.py   # Main .wwp/.wdp parser (streaming)
│   │   ├── wwh_parser.py       # Web page parsing
│   │   ├── wdg_parser.py       # Procedure group parsing
│   │   ├── wdc_parser.py       # Class parsing
│   │   ├── xdd_parser.py       # Database schema parsing
│   │   ├── element_enricher.py # Multi-source data combining
│   │   ├── dependency_extractor.py  # Dependency edge extraction
│   │   ├── global_state_extractor.py# Global variable detection
│   │   ├── pdf_doc_splitter.py # Documentation PDF splitting
│   │   ├── pdf_element_parser.py# PDF element extraction
│   │   ├── query_parser.py     # Query/SQL parsing
│   │   ├── query_enricher.py   # Query enrichment
│   │   ├── compile_if_extractor.py# Conditional compilation
│   │   └── line_reader.py      # Streaming line reader
│   ├── models/                 # Pydantic/Beanie data models (2.5k LOC)
│   │   ├── element.py          # Element + ElementType/Layer enums
│   │   ├── control.py          # UI control hierarchy
│   │   ├── control_type.py     # Control type definitions
│   │   ├── procedure.py        # Procedure/function model
│   │   ├── project.py          # Project metadata
│   │   ├── schema.py           # Database schema model
│   │   ├── conversion.py       # Conversion tracking
│   │   ├── class_definition.py # Class definitions
│   │   ├── configuration_context.py # Configuration state
│   │   ├── global_state_context.py # Global variable state
│   │   ├── conversion_config.py # Conversion settings
│   │   ├── import_session.py   # Import session tracking
│   │   └── token_usage.py      # LLM token tracking
│   ├── analyzer/               # Dependency analysis (5.9k LOC)
│   │   ├── dependency_analyzer.py  # Orchestrator
│   │   ├── graph_builder.py    # NetworkX graph construction
│   │   ├── cycle_detector.py   # Circular dependency detection
│   │   ├── topological_sorter.py# Topological ordering
│   │   ├── graph_exporter.py   # DOT/visualization export
│   │   └── models.py           # AnalysisResult dataclass
│   ├── generator/              # Code generation (7.9k LOC)
│   │   ├── orchestrator.py     # Main generator orchestrator
│   │   ├── base.py             # BaseGenerator + ElementFilter
│   │   ├── schema_generator.py # Pydantic models from schema
│   │   ├── domain_generator.py # Python classes from WinDev
│   │   ├── service_generator.py# Services from procedures
│   │   ├── route_generator.py  # FastAPI routes from pages
│   │   ├── api_generator.py    # REST API endpoints
│   │   ├── template_generator.py# Jinja2 templates
│   │   ├── starter_kit.py      # Project skeleton generation
│   │   ├── state_generator.py  # State management setup
│   │   ├── python_config_generator.py # Python config files
│   │   ├── config_generator.py # Configuration generation
│   │   ├── theme_deployer.py   # Theme/skill deployment
│   │   ├── theme_skill_loader.py# Load theme skills
│   │   ├── wlanguage_converter.py# WLanguage → Python conversion
│   │   ├── type_mapper.py      # Type mapping utilities
│   │   ├── result.py           # GenerationResult dataclass
│   │   ├── templates/          # Jinja2 code templates
│   │   │   ├── jinja2/        # Jinja2 template generation
│   │   │   ├── python/        # Python code templates
│   │   │   ├── html/          # HTML component templates
│   │   │   └── deploy/        # Deployment templates
│   │   └── python/             # Python-specific generation
│   │       └── state_generator.py
│   ├── graph/                  # Neo4j integration (10k LOC)
│   │   ├── neo4j_sync.py       # MongoDB → Neo4j synchronization
│   │   ├── neo4j_connection.py # Neo4j driver management
│   │   └── impact_analyzer.py  # Neo4j-based impact analysis
│   ├── llm_converter/          # LLM-based conversion (81k LOC)
│   │   ├── context_builder.py  # Build LLM context
│   │   ├── conversion_tracker.py# Track conversion state
│   │   ├── proposal_generator.py# Generate conversion proposal
│   │   ├── procedure_converter.py# Convert procedures
│   │   ├── page_converter.py   # Convert pages
│   │   ├── output_writer.py    # Write generated files
│   │   ├── response_parser.py  # Parse Claude responses
│   │   ├── spec_context_loader.py# Load spec context
│   │   ├── import_validator.py # Validate imports
│   │   ├── service_output_writer.py# Service output
│   │   ├── service_response_parser.py# Service response parsing
│   │   ├── procedure_context_builder.py# Procedure context
│   │   ├── llm_client.py       # LLM client factory
│   │   ├── models.py           # ConversionContext model
│   │   └── providers/          # LLM provider implementations
│   │       └── anthropic.py    # Claude API provider
│   ├── api/                    # FastAPI routes
│   │   ├── projects.py         # Project CRUD endpoints
│   │   ├── elements.py         # Element query endpoints
│   │   ├── conversions.py      # Conversion + WebSocket
│   │   ├── import_wizard.py    # Import workflow endpoints
│   │   ├── import_wizard_ws.py # Import WebSocket
│   │   └── websocket.py        # Chat agent WebSocket
│   ├── services/               # High-level business logic
│   │   ├── project_service.py  # Project CRUD service
│   │   ├── conversion_executor.py# Run generation pipeline
│   │   ├── gsd_context_collector.py# Collect GSD context
│   │   ├── gsd_conversion_executor.py# GSD conversion
│   │   ├── gsd_invoker.py      # Claude Code CLI invoker
│   │   ├── chat_agent.py       # Chat message handling
│   │   ├── message_classifier.py# Route messages
│   │   ├── step_executor.py    # Execute conversion steps
│   │   ├── token_tracker.py    # Track token usage
│   │   ├── claude_bridge.py    # Claude API bridge
│   │   ├── guardrail.py        # Safety checks
│   │   ├── output_sanitizer.py # Sanitize outputs
│   │   └── __init__.py         # Service exports
│   ├── transpiler/             # WinDev language transpiling
│   │   └── hyperfile_catalog.py# HyperFile type catalog
│   ├── converter/              # Stack-specific converters
│   │   └── fastapi_jinja/      # FastAPI+Jinja2 converter
│   └── llm_converter/templates # Templates for code generation
├── tests/                      # Test suite
│   ├── test_*.py              # Unit tests for components
│   ├── parser/                # Parser-specific tests
│   │   └── test_project_mapper.py
│   └── integration/           # Integration tests
│       ├── test_binding_extraction.py
│       ├── test_database_connections_pipeline.py
│       └── test_dashlite_theme.py
├── themes/                    # UI framework themes
│   └── dashlite-v3.3.0/      # Bootstrap template theme
├── skills/                    # Reusable skill modules for code gen
├── frontend/                  # Next.js React frontend
│   ├── src/                  # React components
│   ├── public/               # Static assets
│   └── package.json          # Frontend dependencies
├── output/                    # Build artifacts
│   ├── generated/            # Generated code output
│   ├── gsd-context/          # GSD context collections
│   ├── pdf_docs/             # Split documentation
│   └── screenshots/          # Test/demo screenshots
├── project-refs/             # Reference projects for testing
│   └── Linkpay_ADM/          # Example WinDev project
├── uploads/                  # User-uploaded files
├── scripts/                  # Utility scripts
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # MongoDB + Neo4j stack
├── pyproject.toml           # Project metadata
├── pytest.ini               # Pytest configuration
├── setup.py                 # Package setup
├── CLAUDE.md                # Claude AI instructions (this project)
├── README.md                # Project readme
├── CLI-REFERENCE.md         # CLI documentation
└── TODO.md                  # Informal backlog
```

## Key File Locations

### Entry Points

**CLI Entry:**
- `src/wxcode/cli.py` - Typer CLI app with all commands (162k)
- Invoked: `wxcode [command]`

**API Entry:**
- `src/wxcode/main.py` - FastAPI app initialization (91 lines)
- Invoked: `python -m wxcode.main` or `uvicorn wxcode.main:app`

**Configuration:**
- `src/wxcode/config.py` - Settings from environment variables
- Loaded by: main.py, cli.py
- Environment: `.env` file at project root

### Core Processing

**Parser Pipeline:**
- `src/wxcode/parser/project_mapper.py` - .wwp/.wdp streaming extraction (673 lines)
- `src/wxcode/parser/element_enricher.py` - Multi-source data combining (1k+ lines)
- `src/wxcode/parser/dependency_extractor.py` - Extract edges (316 lines)

**Analysis Pipeline:**
- `src/wxcode/analyzer/dependency_analyzer.py` - Orchestrator (324 lines)
- `src/wxcode/analyzer/graph_builder.py` - NetworkX construction (396 lines)
- `src/wxcode/analyzer/topological_sorter.py` - Order calculation (278 lines)

**Generation Pipeline:**
- `src/wxcode/generator/orchestrator.py` - Generator coordinator (1k+ lines)
- `src/wxcode/generator/schema_generator.py` - Pydantic models (476 lines)
- `src/wxcode/generator/template_generator.py` - Jinja2 templates (925 lines)

**LLM Conversion:**
- `src/wxcode/llm_converter/context_builder.py` - Build context (589 lines)
- `src/wxcode/llm_converter/proposal_generator.py` - Generate proposal (389 lines)
- `src/wxcode/services/gsd_invoker.py` - Claude Code CLI invocation (1k+ lines)

### Data Models

**Root Models:**
- `src/wxcode/models/element.py` - Element + enums (379 lines)
- `src/wxcode/models/project.py` - Project document (112 lines)

**Detail Models:**
- `src/wxcode/models/control.py` - UI control hierarchy (498 lines)
- `src/wxcode/models/procedure.py` - Procedure/function (191 lines)
- `src/wxcode/models/schema.py` - Database schema (179 lines)

**State Models:**
- `src/wxcode/models/configuration_context.py` - Config state (215 lines)
- `src/wxcode/models/global_state_context.py` - Global vars (144 lines)

### Database and API

**Database:**
- `src/wxcode/database.py` - Beanie initialization with all models (56 lines)

**API Routes:**
- `src/wxcode/api/projects.py` - Project CRUD
- `src/wxcode/api/elements.py` - Element queries
- `src/wxcode/api/conversions.py` - Conversion + WebSocket (30k+ code, major)
- `src/wxcode/api/import_wizard.py` - Import workflow

### Services

**High-level Orchestration:**
- `src/wxcode/services/project_service.py` - Project operations
- `src/wxcode/services/conversion_executor.py` - Pipeline execution
- `src/wxcode/services/gsd_invoker.py` - Claude Code integration (1k+)

**LLM Interaction:**
- `src/wxcode/services/chat_agent.py` - Message routing
- `src/wxcode/services/step_executor.py` - Step execution
- `src/wxcode/services/token_tracker.py` - Usage tracking

## Naming Conventions

### Files

**Pattern: `{feature}_{subcomponent}.py` or `{function}.py`**

Examples:
- `project_mapper.py` - ProjectElementMapper class
- `element_enricher.py` - ElementEnricher class
- `dependency_analyzer.py` - DependencyAnalyzer class
- `neo4j_sync.py` - Neo4jSync class
- `context_builder.py` - ContextBuilder class

**Generator files:** `{layer}_generator.py`
- `schema_generator.py`
- `domain_generator.py`
- `route_generator.py`

### Directories

**By responsibility:**
- `parser/` - Extraction and parsing
- `models/` - Data models (Pydantic/Beanie)
- `analyzer/` - Dependency analysis
- `generator/` - Code generation
- `graph/` - Graph databases (Neo4j)
- `llm_converter/` - LLM integration
- `api/` - FastAPI routes
- `services/` - Business logic
- `transpiler/` - Language transpilation

**Generator templates:**
- `generator/templates/python/` - Python code templates
- `generator/templates/jinja2/` - Jinja2 template generators
- `generator/templates/html/` - HTML components
- `generator/templates/deploy/` - Deployment files

### Classes

**Pattern: PascalCase, descriptive verb + noun**

Examples:
- `ProjectElementMapper` - Maps project elements
- `ElementEnricher` - Enriches elements with data
- `DependencyAnalyzer` - Analyzes dependencies
- `SchemaGenerator` - Generates schema
- `ContextBuilder` - Builds context
- `ConversionConnectionManager` - Manages WebSocket connections

### Functions/Methods

**Pattern: snake_case, verb + noun**

Examples:
- `parse_project()` - Main parsing method
- `extract_procedures()` - Extract procedures
- `build_graph()` - Build dependency graph
- `generate_schema()` - Generate schema files
- `analyze_impact()` - Analyze change impact

### Constants

**Pattern: UPPER_CASE with underscore separators**

Examples:
- `WINDEV_TYPE_MAP` - Type mapping dictionary
- `TYPE_LAYER_MAP` - Layer mapping
- `GENERATOR_ORDER` - Execution order list
- `MAX_HISTORY_SIZE` - Maximum buffer size

### Enums

**Pattern: PascalCase, plural or descriptive**

Examples:
- `ElementType` - Types of elements
- `ElementLayer` - Conversion layers
- `ConversionStatus` - Conversion states
- `ParserState` - Parser state machine

## Where to Add New Code

### New WinDev File Format Parser

**Location:** `src/wxcode/parser/{format}_parser.py`

**Steps:**
1. Create parser class inheriting from any base or standalone
2. Add type mapping to `src/wxcode/parser/project_mapper.py` (EXTENSION_TYPE_MAP)
3. Call parser from `element_enricher.py` pipeline
4. Add tests in `tests/parser/test_{format}_parser.py`

### New Code Generator

**Location:** `src/wxcode/generator/{layer}_generator.py`

**Steps:**
1. Create class inheriting `BaseGenerator`
2. Implement `generate()` method (async)
3. Use Jinja2 templates from `generator/templates/`
4. Register in `GeneratorOrchestrator.GENERATOR_ORDER` list
5. Add tests in `tests/test_{layer}_generator.py`

**Template location:** `src/wxcode/generator/templates/{language}/{component}.j2`

### New API Endpoint

**Location:** `src/wxcode/api/{feature}.py`

**Steps:**
1. Create router: `router = APIRouter()`
2. Add route functions with FastAPI decorators
3. Include in `src/wxcode/main.py`: `app.include_router(router, prefix=...)`
4. Add tests in `tests/test_{feature}.py`

### New Data Model

**Location:** `src/wxcode/models/{entity}.py`

**Steps:**
1. Create Pydantic model (or Beanie Document for persistence)
2. Add type hints, docstrings, Field descriptions
3. Export from `src/wxcode/models/__init__.py`
4. Register in `src/wxcode/database.py` if Document
5. Add tests validating serialization

### New CLI Command

**Location:** Added to `src/wxcode/cli.py`

**Pattern:**
```python
@app.command("new-command")
def new_command(
    arg1: str = typer.Argument(..., help="Description"),
    opt1: str = typer.Option("default", "--option", help="Description"),
) -> None:
    """Command description."""
    async def _command() -> None:
        # Implementation
        pass
    asyncio.run(_command())
```

### New Service/Business Logic

**Location:** `src/wxcode/services/{service_name}.py`

**Pattern:**
```python
class MyService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def operation(self, param: str) -> Result:
        """Docstring with purpose."""
        # Implementation
```

### Shared Utilities

**Location:**
- String/type utilities → `src/wxcode/generator/type_mapper.py`
- Language conversion → `src/wxcode/generator/wlanguage_converter.py`
- Constants/mappings → Top of relevant module or `src/wxcode/transpiler/`

## Testing Organization

**Structure:** Mirrors source structure with `test_` prefix

```
tests/
├── test_parser.py              # Parser integration tests
├── test_analyzer.py            # Analyzer tests
├── test_generator.py           # Generator tests
├── test_schema_generator.py    # Specific generators
├── test_template_generator.py
├── test_orchestrator.py        # Orchestrator tests
├── parser/                     # Parser-specific tests
│   └── test_project_mapper.py
├── integration/                # Full pipeline tests
│   ├── test_binding_extraction.py
│   └── test_database_connections_pipeline.py
└── __init__.py
```

**Run:** `pytest tests/` or `pytest tests/test_*.py`

**Coverage:** `pytest --cov=src/wxcode tests/`

## Output Generation Paths

**Generated code location:**
- `output/generated/src/schemas/` - Pydantic models
- `output/generated/src/domains/` - Python classes
- `output/generated/src/services/` - Business logic
- `output/generated/src/routes/` - Page routes
- `output/generated/src/api/` - REST endpoints
- `output/generated/templates/` - Jinja2 templates
- `output/generated/main.py` - FastAPI app
- `output/generated/config.py` - Configuration

**GSD context location:**
- `output/gsd-context/{element_name}/element.json` - Element data
- `output/gsd-context/{element_name}/dependencies.json` - Neo4j context
- `output/gsd-context/{element_name}/CONTEXT.md` - Master context file

## Generated/Ignored Directories

**Generated (committed: NO):**
- `output/` - Build artifacts
- `uploads/` - User files
- `src/wxcode.egg-info/` - Package metadata
- `__pycache__/`, `.pytest_cache/` - Python cache

**Configuration/Infrastructure (committed: YES):**
- `docs/` - Documentation
- `openspec/` - Specifications
- `themes/` - UI themes
- `tests/` - Test suite
- `scripts/` - Build/deploy scripts

---

*Structure analysis: 2026-01-21*
