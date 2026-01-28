---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/services/project_service.py
type: service
updated: 2026-01-21
status: active
---

# project_service.py

## Purpose

Provides project management operations including purging (complete deletion of project and all related documents) and duplicate checking. Handles cascading deletes across all related collections (elements, controls, procedures, classes, schema, conversions). Service layer between API and database operations.

## Exports

- `ProjectService` - Class for project management operations
- `purge_project(project_id)` - Delete project and all related documents
- `check_duplicate(project_name)` - Check if project name already exists
- `get_project_stats(project_id)` - Get element/conversion counts

## Dependencies

- [[src-wxcode-models-project]] - Project document
- [[src-wxcode-models-element]] - Element deletion
- [[src-wxcode-models-control]] - Control deletion
- [[src-wxcode-models-procedure]] - Procedure deletion
- [[src-wxcode-models-class_definition]] - ClassDefinition deletion
- [[src-wxcode-models-schema]] - DatabaseSchema deletion
- [[src-wxcode-models-conversion]] - Conversion deletion

## Used By

TBD
