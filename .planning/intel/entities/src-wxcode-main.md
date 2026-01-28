---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/main.py
type: api
updated: 2026-01-21
status: active
---

# main.py

## Purpose

FastAPI application entry point for the WXCODE REST API. Manages application lifecycle including database connection initialization and cleanup. Configures CORS middleware for frontend access and registers all API routers for projects, elements, conversions, chat websocket, and import wizard functionality.

## Exports

- `app` - FastAPI application instance
- `lifespan(app)` - Async context manager for database lifecycle
- `root()` - Root endpoint returning API info
- `health()` - Health check endpoint

## Dependencies

- [[src-wxcode-config]] - Application settings via get_settings()
- [[src-wxcode-database]] - Database initialization (init_db, close_db)
- [[src-wxcode-api-projects]] - Projects router
- [[src-wxcode-api-elements]] - Elements router
- [[src-wxcode-api-conversions]] - Conversions router
- [[src-wxcode-api-websocket]] - WebSocket router
- [[src-wxcode-api-import_wizard]] - Import wizard router
- [[src-wxcode-api-import_wizard_ws]] - Import wizard WebSocket router
- fastapi - Web framework
- dotenv - Environment variable loading

## Used By

TBD
