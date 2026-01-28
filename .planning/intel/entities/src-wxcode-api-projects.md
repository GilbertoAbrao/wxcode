---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/api/projects.py
type: api
updated: 2026-01-21
status: active
---

# projects.py

## Purpose

FastAPI router providing REST endpoints for project management. Supports CRUD operations: list all projects, get project details with statistics, create new projects, update project settings, and delete projects with cascading cleanup. Returns project data with element counts and conversion progress.

## Exports

- `router` - FastAPI APIRouter with project endpoints
- `GET /` - List all projects
- `GET /{project_id}` - Get project details
- `POST /` - Create new project
- `PUT /{project_id}` - Update project
- `DELETE /{project_id}` - Delete project and related data

## Dependencies

- [[src-wxcode-models-project]] - Project document model
- [[src-wxcode-services-project_service]] - Project management operations
- fastapi - Router, HTTPException, status codes

## Used By

TBD
