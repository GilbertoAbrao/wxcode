---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/compile_if_extractor.py
type: module
updated: 2026-01-21
status: active
---

# compile_if_extractor.py

## Purpose

Extracts COMPILE IF blocks from WLanguage code that control conditional compilation for different platforms (Server, Browser, Android, iOS). Identifies platform-specific code sections to enable proper splitting during conversion to appropriate targets.

## Exports

- `CompileIfExtractor` - Class for extracting COMPILE IF blocks
- `extract_compile_blocks(code)` - Find all COMPILE IF sections with conditions
- `CompileBlock` - Dataclass representing a conditional compilation block

## Dependencies

- re - Regular expression for block detection
- dataclasses - CompileBlock definition

## Used By

TBD
