---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/project.py
type: model
updated: 2026-01-21
status: active
---

# project.py

## Purpose

Defines the Project Beanie document model representing a WinDev/WebDev project in MongoDB. Stores project metadata including name, version, source path, configuration settings, and global context. Serves as the root document linking all elements, procedures, and conversions.

## Exports

- `ProjectConfiguration` - Pydantic model for project-level settings (debug, API host/port)
- `Project` - Beanie Document for project storage with fields: name, version, source_path, configuration, global_context, created_at, updated_at

## Dependencies

- beanie - Document ODM
- pydantic - Data validation
- datetime - Timestamp fields

## Used By

TBD
