---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/elements.py
type: api
updated: 2026-01-21
status: active
---

# elements.py

## Purpose

FastAPI router providing REST endpoints for element management. Supports listing elements with filtering by type/layer/status, getting element details including AST and dependencies, and updating element conversion status. Enables frontend to browse and inspect project elements.

## Exports

- `router` - FastAPI APIRouter with element endpoints
- `GET /` - List elements with optional filters (type, layer, status, project_id)
- `GET /{element_id}` - Get element details with full AST and dependencies
- `PATCH /{element_id}` - Update element conversion status

## Dependencies

- [[src-wxcode-models-element]] - Element document model
- [[src-wxcode-models-project]] - Project reference
- fastapi - Router, Query parameters, HTTPException

## Used By

TBD
