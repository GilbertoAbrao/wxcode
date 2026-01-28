---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/wwp_parser.py
type: module
updated: 2026-01-21
status: active
---

# wwp_parser.py

## Purpose

Parses WinDev project files (.wwp) to extract project metadata and element list. Handles the YAML-like WinDev file format with hierarchical sections. Yields elements as they are discovered for streaming processing. Core parser for project structure discovery.

## Exports

- `WWPParser` - Class for parsing .wwp project files
- `parse_wwp(file_path)` - Generator yielding project elements with metadata

## Dependencies

- pathlib - File path handling
- re - Regular expression parsing for WinDev format

## Used By

TBD
