---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/import_session.py
type: model
updated: 2026-01-21
status: active
---

# import_session.py

## Purpose

Defines ImportSession Beanie document for tracking import wizard sessions. Manages multi-step import workflow state including source path, project selection, PDF mapping, and import progress. Supports resumable imports and error recovery.

## Exports

- `ImportStep` - Enum for wizard steps (SELECT_SOURCE, MAP_PDF, CONFIGURE, IMPORTING, COMPLETE)
- `ImportSession` - Beanie Document with session_id, current step, source paths, progress tracking

## Dependencies

- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
