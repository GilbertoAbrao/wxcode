---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/llm_converter/providers/prompts.py
type: util
updated: 2026-01-21
status: active
---

# prompts.py

## Purpose

Contains system prompts for LLM-based code conversion. Defines detailed prompts for converting WinDev pages to Jinja2 templates, procedures to Python services, and classes to Pydantic models. Includes WLanguage-to-Python mapping reference, coding conventions, and output format specifications.

## Exports

- `PAGE_CONVERSION_PROMPT` - System prompt for page-to-template conversion
- `PROCEDURE_CONVERSION_PROMPT` - System prompt for procedure-to-service conversion
- `CLASS_CONVERSION_PROMPT` - System prompt for class-to-model conversion
- `get_conversion_prompt(element_type)` - Get appropriate prompt for element type

## Dependencies

- None (pure string constants)

## Used By

TBD
