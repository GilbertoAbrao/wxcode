# External Integrations

**Analysis Date:** 2026-01-21

## APIs & External Services

**LLM Providers (Pluggable):**
- Anthropic Claude - Intelligent code conversion
  - SDK/Client: `anthropic` 0.75.0
  - Auth: `ANTHROPIC_API_KEY` environment variable
  - Default model: `claude-sonnet-4-20250514`
  - Alternative models: `claude-opus-4-20250514`, `claude-3-5-haiku-20241022`
  - Location: `src/wxcode/llm_converter/providers/anthropic.py`
  - Usage: Converts WinDev procedures to Python, generates templates, provides intelligent suggestions

- OpenAI GPT - Alternative LLM provider
  - SDK/Client: `openai` (optional)
  - Auth: `OPENAI_API_KEY` environment variable
  - Default model: `gpt-4o`
  - Location: `src/wxcode/llm_converter/providers/openai.py`
  - Note: Optional integration, requires explicit `pip install openai`

- Ollama (Local LLM) - On-premise model support
  - SDK/Client: httpx calls to local Ollama server
  - Base URL: `OLLAMA_BASE_URL` or `http://localhost:11434`
  - Default models: llama3.1, mistral, codellama, deepseek-coder
  - Location: `src/wxcode/llm_converter/providers/ollama.py`
  - Note: No API key required, runs locally

**n8n ChatAgent Webhook:**
- URL: `N8N_WEBHOOK_URL` environment variable
- Default: `https://botfy-ai-agency-n8n.tb0oe2.easypanel.host/webhook/chat-agent-v2`
- Purpose: Process Claude Code output and generate chat agent responses
- Integration point: `src/wxcode/services/gsd_invoker.py` (lines 330-401, 696-767)
- HTTP Method: POST
- Content-Type: application/json
- Timeout: 30 seconds (httpx.AsyncClient timeout)
- Fallback: If n8n unavailable, extracts text directly and sends via WebSocket

## Data Storage

**Databases:**

**MongoDB:**
- Connection: `MONGODB_URL` (default: `mongodb://localhost:27017`)
- Database: `MONGODB_DATABASE` (default: `wxcode`)
- Client: Motor 3.7.1 (async) with Beanie 2.0.1 (ODM)
- Connection init: `src/wxcode/database.py`
- Document models stored in `src/wxcode/models/`
  - Project - Metadata about WinDev projects
  - Element - Individual elements (pages, procedures, classes, etc.)
  - Conversion - Conversion status and results
  - Control - UI controls and their properties
  - ControlTypeDefinition - Control type definitions
  - Procedure - Procedure definitions
  - DatabaseSchema - Database schema information
  - ClassDefinition - Class definitions
  - TokenUsageLog - Token usage tracking for cost monitoring
  - ImportSession - Import session state
- Operations: Async queries via Beanie, batch writes (100 document default)

**Neo4j:**
- Connection: `NEO4J_URI` (default: `bolt://localhost:7687`)
- Authentication: `NEO4J_USER` and `NEO4J_PASSWORD`
- Database: `NEO4J_DATABASE` (default: `neo4j`)
- Client: Neo4j 5.28.1 async driver
- Connection class: `src/wxcode/graph/neo4j_connection.py`
- Purpose: Stores dependency graph (elements and their relationships)
- Async operations: Query execution, batch node creation, impact analysis
- Features: Index creation on demand, clear by project, statistics retrieval
- Used by: Dependency analysis, impact assessment, topological sorting

**File Storage:**
- Local filesystem only - no cloud storage integration
- Upload directories: `uploads/` folder for project imports
- Output directories:
  - `output/generated/` - Generated code output
  - `output/gsd-context/` - GSD context files (JSON + CONTEXT.md)
  - `output/pdf_docs/` - Split PDF documentation

## Caching

**Token Caching:**
- Location: `src/wxcode/config.py` - Settings class with `@lru_cache` decorator
- Purpose: Cache environment-based configuration across requests
- Method: Python's functools.lru_cache

**Database Connection Pooling:**
- Motor: Manages async connection pool automatically
- Neo4j: Configurable pool size (max_connection_pool_size=50 in `neo4j_connection.py`)

**No distributed cache system** - Relies on application memory for session data

## Authentication & Identity

**Auth Provider:**
- Custom/None - No centralized auth system in place
- CORS configured for development (localhost only)
- API endpoints unprotected (suitable for development/internal use)

**API Key Management:**
- Environment variables store sensitive keys
- .env file recommended for local development
- No secrets management service integrated (no Vault, AWS Secrets, etc.)

**Required API Keys:**
- `ANTHROPIC_API_KEY` - For Claude API calls
- `NEO4J_PASSWORD` - For Neo4j authentication
- `OPENAI_API_KEY` - Optional, if using OpenAI provider

## Monitoring & Observability

**Error Tracking:**
- Not detected - No Sentry, Rollbar, or similar service integration
- Errors logged to console/standard output via Python logging

**Logs:**
- Approach: Python standard `logging` module
- Log level configurable via `LOG_LEVEL` environment variable (default: INFO)
- Used throughout codebase:
  - `logger.info()` - Informational messages
  - `logger.warning()` - Warnings (e.g., database operations)
  - `logger.error()` - Errors

**Output Formatting:**
- Rich library for colored terminal output (progress bars, panels, tables)
- Location: Used in CLI and services (`src/wxcode/services/gsd_invoker.py`)

**Token Usage Tracking:**
- Stored in MongoDB `TokenUsageLog` collection
- Location: `src/wxcode/models/token_usage.py`
- Logs input/output tokens per LLM API call for cost monitoring

## CI/CD & Deployment

**Hosting:**
- Not specified - This is a backend service, intended to be self-hosted
- Deployment target: Linux server with Python 3.11+, MongoDB, Neo4j
- Docker support recommended but not included in repo

**CI Pipeline:**
- Not detected - No GitHub Actions, GitLab CI, Jenkins, etc. configuration found
- Pre-commit hooks available via `pre-commit` framework (ruff, mypy, etc.)

**Entry Points:**
- CLI: `wxcode` command via entry point `src/wxcode/cli.py`
- API: FastAPI app startup via `src/wxcode/main.py` (Uvicorn)
- Web server: localhost:8035 (configurable)

## Environment Configuration

**Required Environment Variables:**
- `MONGODB_URL` - MongoDB connection string
- `MONGODB_DATABASE` - Database name
- `ANTHROPIC_API_KEY` - Anthropic API key (for Claude conversions)
- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_USER` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password

**Optional Environment Variables:**
- `DEBUG` - Debug mode (default: false)
- `LOG_LEVEL` - Logging level (default: INFO)
- `API_HOST` - FastAPI host (default: 0.0.0.0)
- `API_PORT` - FastAPI port (default: 8000)
- `DEFAULT_TARGET_STACK` - Target conversion stack (default: fastapi-jinja2)
- `MAX_TOKENS_PER_CHUNK` - Token threshold for chunking (default: 3500)
- `CHUNK_OVERLAP_TOKENS` - Overlap between chunks (default: 200)
- `CONVERSION_PROVIDER` - LLM provider selection (default: anthropic)
- `CONVERSION_MODEL` - LLM model override
- `OPENAI_API_KEY` - OpenAI API key (if using OpenAI provider)
- `OLLAMA_BASE_URL` - Ollama server URL (if using local models)
- `N8N_WEBHOOK_URL` - n8n ChatAgent webhook for message processing

**Secrets Location:**
- .env file (not committed, use .env.example as template)
- Environment variables at runtime
- No dedicated secrets management service configured

## Webhooks & Callbacks

**Incoming Webhooks:**
- `/api/import-wizard/ws` - WebSocket for import progress streaming
  - Location: `src/wxcode/api/import_wizard_ws.py`
  - Emits: Progress events, status updates during project import

- `/api/chat` - WebSocket for Claude Code execution output
  - Location: `src/wxcode/api/websocket.py`
  - Emits: Logs, LLM responses, execution results, chat messages from n8n

- `/api/import-wizard` - REST endpoints for import workflow
  - Location: `src/wxcode/api/import_wizard.py`
  - Methods: POST for triggering imports, GET for session status

**Outgoing Webhooks:**
- n8n ChatAgent webhook (POST)
  - URL: Environment variable `N8N_WEBHOOK_URL`
  - Payload: JSON message object (type, content, options, confidence, timestamp)
  - Purpose: Process Claude Code LLM responses and generate agent chat responses
  - Async call via httpx from `src/wxcode/services/gsd_invoker.py`

**WebSocket Connections:**
- Server emits logs, chat messages, progress updates to connected clients
- Client can send user messages (resume/continue prompts)
- Bi-directional communication for real-time streaming

## PDF Processing

**PDF Tools:**
- pdfplumber 0.11.8 - Main PDF parsing and table extraction
- pdfminer.six 20251107 - Text extraction fallback
- PyMuPDF 1.26.7 - Alternative PDF library for complex documents
- pypdfium2 5.2.0 - Utility functions for PDF processing
- Pillow 12.0.0 - Image conversion if PDFs contain images

**Location:**
- Parser: `src/wxcode/parser/pdf_doc_splitter.py` - Splits documentation into individual PDFs
- Enricher: `src/wxcode/parser/pdf_element_parser.py` - Extracts content from PDFs for enrichment

## Code Generation Targets

**Output Stacks:**
- FastAPI + Jinja2 (primary)
  - Generator: `src/wxcode/generator/fastapi_jinja/`
  - Generates: Python service classes, FastAPI routes, Jinja2 templates

**Conversion Quality:**
- Uses Claude LLM for intelligent conversion
- Manual review workflow for complex conversions
- Cost tracking via TokenUsageLog

---

*Integration audit: 2026-01-21*
