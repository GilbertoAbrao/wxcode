---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/models/class_definition.py
type: model
updated: 2026-01-21
status: active
---

# class_definition.py

## Purpose

Defines the ClassDefinition Beanie document representing WLanguage classes extracted from .wdc files. Stores class name, base class (inheritance), member properties with types, methods as procedures, and raw WLanguage content. Supports domain layer conversion to Python classes.

## Exports

- `ClassMember` - Pydantic model for class properties with name, type, visibility, default value
- `ClassDefinition` - Beanie Document with class structure, methods, inheritance, and source info

## Dependencies

- [[src-wxcode-models-project]] - Project link
- [[src-wxcode-models-procedure]] - Method definitions as Procedure models
- beanie - Document ODM
- pydantic - Data validation

## Used By

TBD
