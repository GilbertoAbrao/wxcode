---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/conversion.py
type: model
updated: 2026-01-21
status: active
---

# conversion.py

## Purpose

Defines the Conversion Beanie document for tracking entire project conversion processes. Monitors conversion phases (PENDING through COMPLETED), progress per layer (schema, domain, business, API, UI), error collection, and timing metrics. Provides overall progress calculation and duration tracking.

## Exports

- `ConversionPhase` - Enum for pipeline phases (PENDING, SCHEMA, DOMAIN, BUSINESS, API, UI, VALIDATION, COMPLETED, ERROR)
- `ConversionError` - Pydantic model for errors with element info, phase, message, recoverability
- `LayerProgress` - Pydantic model tracking total/converted/validated/errors per layer
- `Conversion` - Beanie Document with full conversion tracking and computed properties

## Dependencies

- [[src-wxcode-models-project]] - Project link reference
- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
