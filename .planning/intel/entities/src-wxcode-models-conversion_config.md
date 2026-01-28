---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/conversion_config.py
type: model
updated: 2026-01-21
status: active
---

# conversion_config.py

## Purpose

Defines Pydantic models for conversion configuration options. Specifies target stack settings, element filtering rules, output directory preferences, and conversion behavior flags used by the generator orchestrator.

## Exports

- `TargetStack` - Enum for supported output stacks (FASTAPI_JINJA2, etc.)
- `ConversionConfig` - Pydantic model with target_stack, output_dir, element_filter, options

## Dependencies

- pydantic - Data validation and BaseModel

## Used By

TBD
