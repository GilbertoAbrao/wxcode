# Architecture

**Analysis Date:** 2026-01-21

## System Overview

WXCODE is a universal converter for WinDev/WebDev/WinDev Mobile projects to modern stacks. It implements a **multi-stage pipeline architecture** that transforms legacy WinDev code into FastAPI + Jinja2 applications.

**Core flow:** Extract (WinDev → MongoDB) → Analyze (dependency graph) → Generate (models/services/routes/templates)

## Architectural Pattern

**Layered Pipeline Architecture with Streaming I/O**

- **Extraction Layer**: Streaming parsers read WinDev project files (.wwp, .wwh, .wdg, .wdc, .wdd)
- **Persistence Layer**: MongoDB stores intermediate representations (Element, Control, Procedure models)
- **Analysis Layer**: Dependency graph construction (NetworkX + Neo4j)
- **Generation Layer**: Code generators orchestrated in topological order
- **API Layer**: FastAPI REST + WebSocket endpoints for project management and conversions
- **LLM Layer**: Claude-based intelligent conversion of complex procedures

## Layers and Components

### 1. Parser Layer
**Location:** `src/wxcode/parser/`

**Purpose:** Extract structured data from binary WinDev project files using streaming to handle 100k+ line files efficiently.

**Components:**
- `project_mapper.py` - Main orchestrator, state machine parser for .wwp/.wdp files
- `wwh_parser.py` - Web page parsing (controls, events, procedures)
- `wdg_parser.py` - Procedure group parsing (server-side procedures)
- `wdc_parser.py` - Class definition parsing
- `xdd_parser.py` - Database schema parsing
- `element_enricher.py` - Combines multiple data sources (WWH + PDF + procedures)
- `dependency_extractor.py` - Extracts element-to-element dependencies
- `global_state_extractor.py` - Identifies global variables and state
- `pdf_doc_splitter.py` - Splits documentation PDFs into elements

**Key Pattern:** Streaming with MongoDB batch insertion (default batch size: 100)

### 2. Data Model Layer
**Location:** `src/wxcode/models/`

**Purpose:** Pydantic/Beanie models for MongoDB persistence with type hints and validation.

**Core Models:**
- `element.py` - Element (page, procedure, class, query); ElementType, ElementLayer, ConversionStatus enums
- `control.py` - UI controls hierarchy, properties, events, data bindings
- `control_type.py` - Control type definitions and metadata
- `procedure.py` - Procedures with AST representation
- `schema.py` - Database schema with tables, columns, types
- `project.py` - Project metadata and configuration
- `conversion.py` - Conversion tracking and results
- `class_definition.py` - Class definitions with inheritance

**Database:** MongoDB with Beanie async ODM (Motor driver)

### 3. Analyzer Layer
**Location:** `src/wxcode/analyzer/` and `src/wxcode/graph/`

**Purpose:** Build dependency graphs and determine topological conversion order.

**Components:**
- `graph_builder.py` - Constructs NetworkX DiGraph from MongoDB elements
- `cycle_detector.py` - Detects circular dependencies
- `topological_sorter.py` - Orders elements by layer (SCHEMA → DOMAIN → BUSINESS → API → UI)
- `dependency_analyzer.py` - Orchestrator for complete analysis
- `graph_exporter.py` - Exports to DOT format for visualization
- `neo4j_sync.py` - Synchronizes graph to Neo4j for advanced analysis
- `impact_analyzer.py` - Neo4j-based impact analysis (what changes if element X changes?)

**Flow:**
1. Extract element-to-element dependencies from AST
2. Build directed graph
3. Detect cycles (circular dependencies must be broken)
4. Sort topologically to determine safe conversion order
5. Persist order in MongoDB for generation step

### 4. LLM Conversion Layer
**Location:** `src/wxcode/llm_converter/`

**Purpose:** Intelligent code conversion using Claude for complex procedures and pages.

**Components:**
- `context_builder.py` - Assembles MongoDB data + related elements + schema into conversation context
- `proposal_generator.py` - Generates conversion proposals via Claude
- `procedure_converter.py` - Converts WLanguage procedures to Python
- `page_converter.py` - Converts web pages to HTML/Jinja2
- `conversion_tracker.py` - Tracks LLM token usage and conversion state
- `providers/` - Provider-specific implementations (Anthropic)

**Pattern:** Context is chunked to fit Claude's token window with semantic overlap

### 5. Generator Layer
**Location:** `src/wxcode/generator/`

**Purpose:** Generate code in topological order respecting dependencies.

**Generators (executed in order):**
1. `schema_generator.py` - Pydantic models from DatabaseSchema
2. `domain_generator.py` - Python classes from WinDev classes
3. `service_generator.py` - Python services from WinDev procedures
4. `route_generator.py` - FastAPI routes from WinDev pages
5. `api_generator.py` - REST API routes
6. `template_generator.py` - Jinja2 templates from WinDev pages

**Orchestration:**
- `orchestrator.py` - Runs all generators in order, tracks progress
- `starter_kit.py` - Generates project skeleton (main.py, config, requirements.txt, docker-compose.yml)
- `base.py` - BaseGenerator class with template rendering
- `element_filter.py` - Selective element conversion via ID/name patterns

**Output Structure:**
```
output/generated/
├── src/
│   ├── schemas/       # Generated Pydantic models
│   ├── domains/       # Generated classes
│   ├── services/      # Generated business logic
│   ├── routes/        # Generated FastAPI routes
│   ├── api/           # Generated REST endpoints
│   └── config.py
├── templates/         # Generated Jinja2 templates
├── main.py
├── requirements.txt
└── docker-compose.yml
```

### 6. API Layer
**Location:** `src/wxcode/api/`

**Purpose:** REST + WebSocket endpoints for web UI integration.

**Endpoints:**
- `projects.py` - Project CRUD operations
- `elements.py` - Element queries and filtering
- `conversions.py` - Conversion execution and WebSocket streaming
- `import_wizard.py` - Multi-step import workflow
- `import_wizard_ws.py` - WebSocket for import progress
- `websocket.py` - Chat agent for interactive conversions

**Connection Management:** `ConversionConnectionManager` maintains WebSocket connections per conversion, stores log history for replay on reconnect

### 7. Service Layer
**Location:** `src/wxcode/services/`

**Purpose:** High-level business logic and orchestration.

**Services:**
- `project_service.py` - Project creation/deletion/status
- `conversion_executor.py` - Runs code generation pipeline
- `gsd_invoker.py` - Invokes Claude Code CLI for interactive conversions
- `gsd_context_collector.py` - Collects Neo4j/MongoDB context for GSD workflow
- `chat_agent.py` - Manages message flow with LLM
- `message_classifier.py` - Routes messages to appropriate handlers
- `step_executor.py` - Executes individual conversion steps
- `token_tracker.py` - Tracks LLM token usage per project

### 8. CLI Layer
**Location:** `src/wxcode/cli.py`

**Purpose:** Command-line interface for pipeline operations.

**Main Commands:**
- `import` - Import WinDev project to MongoDB
- `enrich` - Extract controls, procedures, dependencies
- `parse-schema` - Parse database schema
- `parse-procedures` - Parse WinDev procedure files
- `parse-classes` - Parse WinDev class files
- `analyze` - Build dependency graph and export
- `convert` - Generate code in target stack
- `sync-neo4j` - Synchronize MongoDB graph to Neo4j
- `impact` - Analyze change impact via Neo4j
- `gsd-context` - Collect context for Claude Code GSD workflow

## Data Flow

### Import Pipeline (CLI: `wxcode import`)

```
.wwp/.wdp file
    ↓ (ProjectElementMapper streaming)
Extract metadata, element list
    ↓ (batch insert 100 at a time)
MongoDB: Project + Elements (raw_content populated)
    ↓ (CLI: enrich)
Extract controls, procedures, dependency edges
    ↓ (WWH parser, WDG parser)
MongoDB: Element.ast, Control collection, ElementDependencies
    ↓ (CLI: parse-schema)
Extract database schema
    ↓ (XDD parser)
MongoDB: DatabaseSchema collection
    ↓ (CLI: analyze)
Build NetworkX graph, topological sort
    ↓ (DependencyAnalyzer)
MongoDB: Element.topological_order, Element.layer
```

### Generation Pipeline (CLI: `wxcode convert`)

```
MongoDB Elements (sorted by topological_order)
    ↓ (GeneratorOrchestrator)
SchemaGenerator
    → src/schemas/models.py (Pydantic models)
    ↓
DomainGenerator
    → src/domains/classes.py (Python classes)
    ↓
ServiceGenerator
    → src/services/*.py (Business logic)
    ↓
RouteGenerator
    → src/routes/*.py (FastAPI page routes)
    ↓
APIGenerator
    → src/api/*.py (REST endpoints)
    ↓
TemplateGenerator
    → templates/*.html (Jinja2)
    ↓
StarterKit
    → main.py, config.py, docker-compose.yml, etc.
    ↓
output/generated/
```

### Conversion Workflow (API + LLM)

```
POST /api/conversions/start
    ↓ (ContextBuilder)
Load Element + related Elements from MongoDB
Chunk large procedures (3500 tokens default, 200 overlap)
Load theme skills and spec context
    ↓ (Claude API)
Generate proposal (AST → intermediate representation)
    ↓ (ProposalGenerator)
Return structured task breakdown
    ↓ (StepExecutor)
Execute each task (call Claude for each code block)
    ↓ (OutputWriter)
Write generated code to MongoDB + filesystem
    ↓ (GsdInvoker)
Invoke Claude Code CLI with context for interactive refinement
```

## Key Abstractions

### Element (Document)
**File:** `src/wxcode/models/element.py`

Represents any WinDev component: page (.wwh), procedure group (.wdg), class (.wdc), query (.wdr).

**Attributes:**
- `source_name`: Name (e.g., "PAGE_Login")
- `source_type`: ElementType enum
- `source_layer`: ElementLayer enum (SCHEMA, DOMAIN, BUSINESS, API, UI)
- `raw_content`: Full file content
- `chunks`: SemanticChunks for large files
- `ast`: Parsed Abstract Syntax Tree (procedures, variables, controls, events)
- `dependencies`: Element-to-element dependency edges
- `topological_order`: Integer order for conversion
- `conversion`: Status, target files, issues

### ElementDependencies (Embedded)
**File:** `src/wxcode/models/element.py`

Tracks what an element uses and what uses it:
- `uses`: Elements this element depends on
- `used_by`: Elements that depend on this
- `data_files`: Tables referenced
- `external_apis`: External integrations

### Control (Document)
**File:** `src/wxcode/models/control.py`

Represents a UI control in a page (TextEdit, Button, etc.):
- `type_code`: Numeric WinDev type
- `type_definition_id`: Link to ControlTypeDefinition
- `name`: Control name ("EDT_LOGIN")
- `full_path`: Hierarchical path ("CELL1.EDT_LOGIN")
- `parent_control_id`: Container control
- `children_ids`: Child controls
- `properties`: UI properties (height, width, position, etc.)
- `events`: Event handlers with code
- `data_bindings`: Data bindings to schema fields

### Procedure (Embedded in Element)
**File:** `src/wxcode/models/procedure.py`

Represents a procedure/function:
- `name`: Procedure name
- `parameters`: List with names and types
- `returns_type`: Return type
- `code`: Raw WLanguage code
- `local_variables`: Procedure-scope variables
- `calls`: Other procedures this calls
- `event_bindings`: UI events that trigger it

### ConversionContext
**File:** `src/wxcode/llm_converter/models.py`

Context for LLM conversion:
- `element`: The element being converted
- `related_elements`: Nearby elements (up to 50)
- `schema`: Relevant database schema
- `theme_skills`: UI framework skills/patterns
- `spec`: Project conversion specifications
- `chunks`: Chunked code for window-fitting

## Entry Points

### CLI Entry Point
**File:** `src/wxcode/cli.py`

Typer CLI app with commands for each pipeline step. Invoked via `wxcode [command]`.

### API Entry Point
**File:** `src/wxcode/main.py`

FastAPI application with:
- CORS middleware (localhost:3000, :3020)
- Lifespan context manager (DB init/close)
- Route registration (projects, elements, conversions, websocket, import_wizard)
- Health endpoints (`/`, `/health`)

Run: `python -m wxcode.main` or `uvicorn wxcode.main:app`

### GSD Entry Point
**File:** `src/wxcode/services/gsd_invoker.py`

Integrates with Claude Code CLI:
1. Collects context from MongoDB + Neo4j
2. Creates branch `gsd/{element}+{random8}`
3. Writes context files to `output/gsd-context/`
4. Invokes `claude-code-cli /gsd:new-project CONTEXT.md`
5. Monitors subprocess stdout for conversion progress

## Error Handling

**Strategy:** Exceptions propagate with context

**Patterns:**
- **Parser errors:** LogicError with file position and state context
- **Conversion errors:** ConversionError with element_id and issue description
- **Database errors:** Caught at service layer, return HTTP 500 with detail
- **LLM errors:** ConversionError wraps Anthropic API errors, includes partial result

**Logging:** Structured logs to console + optional file with DEBUG/INFO/WARNING/ERROR levels

## Cross-Cutting Concerns

### Logging
**Framework:** Python logging

**Pattern:** Each module initializes logger at top
```python
logger = logging.getLogger(__name__)
logger.info(f"Message with context: {element.source_name}")
```

**Levels used:** DEBUG (parser internals), INFO (pipeline progress), WARNING (recoverable issues), ERROR (failures)

### Validation
**Framework:** Pydantic for models, custom validators for business rules

**Pattern:** All API requests validated by Pydantic request models, all MongoDB documents validated on deserialize

**Example:** `ElementFilter` validates element name patterns support wildcards

### Async/Await
**Pattern:** Async throughout (Motor for MongoDB, async generators for streaming, asyncio subprocess)

**No blocking calls** in async code paths except for logging

### Type Hints
**Requirement:** Type hints on all functions (enforced by mypy)

**Typing imports:** `from typing import Optional, Union, TypeVar, Generic` used throughout

### Constants and Mappings
**Pattern:** Top-level dicts for type mappings

**Examples:**
- `WINDEV_TYPE_MAP`: Numeric type code → ElementType
- `EXTENSION_TYPE_MAP`: File extension → ElementType
- `TYPE_LAYER_MAP`: ElementType → ElementLayer (determines generation order)
- `SchemaGenerator.TYPE_MAP`: HyperFile type codes → Python types

---

*Architecture analysis: 2026-01-21*
