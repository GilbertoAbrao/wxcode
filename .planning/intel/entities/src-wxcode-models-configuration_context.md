---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/configuration_context.py
type: model
updated: 2026-01-21
status: active
---

# configuration_context.py

## Purpose

Defines Pydantic models for configuration intermediate representation (IR). Captures project-level configuration patterns like debug settings, API configuration, and environment variables extracted from WinDev projects for conversion to modern config systems.

## Exports

- `ConfigurationEntry` - Pydantic model for individual config entries with name, value, type
- `ConfigurationContext` - Pydantic model aggregating all configuration for a project

## Dependencies

- pydantic - Data validation and BaseModel

## Used By

TBD
