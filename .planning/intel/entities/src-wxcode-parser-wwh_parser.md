---
path: /Users/gilberto/projetos/wxk/wxcode/src/wxcode/parser/wwh_parser.py
type: module
updated: 2026-01-21
status: active
---

# wwh_parser.py

## Purpose

Parses WinDev page (.wwh) and window (.wdw) files to extract UI controls, events, and local procedures. Builds control hierarchy with parent-child relationships, extracts event handlers with code, and identifies data bindings. Critical for UI layer conversion to Jinja2 templates.

## Exports

- `WWHParser` - Class for parsing page/window files
- `parse_wwh(content)` - Parse page content returning controls, events, procedures
- `extract_controls(content)` - Extract control hierarchy
- `extract_events(content)` - Extract event handlers with code

## Dependencies

- [[src-wxcode-models-control]] - Control document creation
- [[src-wxcode-models-control_type]] - Control type resolution
- re - Regular expression parsing

## Used By

TBD
