---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/import_wizard.py
type: api
updated: 2026-01-21
status: active
---

# import_wizard.py

## Purpose

FastAPI router providing REST endpoints for the multi-step import wizard. Manages import sessions through steps: source selection, PDF mapping, configuration, and import execution. Supports session persistence for resumable imports and file upload handling.

## Exports

- `router` - FastAPI APIRouter with import wizard endpoints
- `POST /sessions` - Create new import session
- `GET /sessions/{session_id}` - Get session state
- `PUT /sessions/{session_id}/source` - Set source project path
- `PUT /sessions/{session_id}/pdf` - Map PDF documentation
- `PUT /sessions/{session_id}/config` - Set import configuration
- `POST /sessions/{session_id}/start` - Start import process

## Dependencies

- [[src-wxcode-models-import_session]] - ImportSession document
- [[src-wxcode-parser-project_mapper]] - Project import execution
- fastapi - Router, UploadFile, Form

## Used By

TBD
