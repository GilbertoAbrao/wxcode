---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/database.py
type: service
updated: 2026-01-21
status: active
---

# database.py

## Purpose

Manages MongoDB connection lifecycle and Beanie ODM initialization. Provides async functions for establishing database connection with all document models and cleanly closing connections. Central database access point for the entire application.

## Exports

- `init_db() -> AsyncIOMotorClient` - Initialize MongoDB connection and Beanie with all document models
- `close_db(client)` - Close MongoDB connection gracefully

## Dependencies

- [[src-wxcode-config]] - Database connection settings
- [[src-wxcode-models-project]] - Project document model
- [[src-wxcode-models-element]] - Element document model
- [[src-wxcode-models-control]] - Control document model
- [[src-wxcode-models-control_type]] - ControlTypeDefinition model
- [[src-wxcode-models-procedure]] - Procedure document model
- [[src-wxcode-models-class_definition]] - ClassDefinition model
- [[src-wxcode-models-schema]] - DatabaseSchema model
- [[src-wxcode-models-conversion]] - Conversion model
- [[src-wxcode-models-token_usage]] - TokenUsage model
- [[src-wxcode-models-import_session]] - ImportSession model
- motor - Async MongoDB driver
- beanie - ODM for MongoDB

## Used By

TBD
