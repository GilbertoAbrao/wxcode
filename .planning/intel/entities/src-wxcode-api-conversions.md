---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/conversions.py
type: api
updated: 2026-01-21
status: active
---

# conversions.py

## Purpose

FastAPI router providing REST endpoints for conversion management with WebSocket streaming. Supports starting conversions with element filtering, monitoring progress via WebSocket, retrieving conversion results, and canceling in-progress conversions. Streams real-time progress updates to frontend.

## Exports

- `router` - FastAPI APIRouter with conversion endpoints
- `POST /` - Start new conversion with optional element filter
- `GET /{conversion_id}` - Get conversion status and progress
- `GET /{conversion_id}/results` - Get generated files
- `DELETE /{conversion_id}` - Cancel conversion
- `WS /{conversion_id}/stream` - WebSocket for real-time progress

## Dependencies

- [[src-wxcode-models-conversion]] - Conversion document model
- [[src-wxcode-models-element]] - Element filtering
- [[src-wxcode-generator-orchestrator]] - Conversion orchestration
- fastapi - Router, WebSocket, BackgroundTasks

## Used By

TBD
