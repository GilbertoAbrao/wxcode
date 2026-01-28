---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/llm_converter/models.py
type: model
updated: 2026-01-21
status: active
---

# models.py (llm_converter)

## Purpose

Defines Pydantic models for LLM-based code conversion workflow. Represents conversion context (input element, dependencies, schema), conversion results (generated files, issues, review flags), and error types. Used by LLM providers to structure prompts and parse responses.

## Exports

- `ConversionContext` - Pydantic model with element, dependencies, schema context for LLM
- `ConversionResult` - Pydantic model with generated files, issues, success flag
- `GeneratedFile` - Pydantic model for individual output file with path and content
- `ConversionError` - Pydantic model for conversion errors with type and message

## Dependencies

- pydantic - Data validation and BaseModel
- [[src-wxcode-models-element]] - Element reference

## Used By

TBD
