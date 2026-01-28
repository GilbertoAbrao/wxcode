---
phase: 20-global-state-extraction
plan: 02
subsystem: services
tags: [prompt-builder, global-state, context-md, api, websocket]

# Dependency graph
requires:
  - phase: 20-01
    provides: extract_global_state_for_project() function
provides:
  - format_global_state() for markdown table with scope annotations
  - format_scope_patterns() for conversion pattern documentation
  - Global State section in CONTEXT.md template
affects: [21-init-context-assembly, gsd-workflow]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Sensitive name detection for credential redaction"
    - "Scope-to-pattern mapping for Python recommendations"
    - "Optional global_state parameter with backward compatibility"

key-files:
  created: []
  modified:
    - src/wxcode/services/prompt_builder.py
    - src/wxcode/api/output_projects.py

key-decisions:
  - "Sensitive variables (token, secret, password, key) have defaults redacted"
  - "Long type names truncated at 30 chars for table readability"
  - "Scope patterns section only shown when global variables exist"

patterns-established:
  - "_is_sensitive_name() helper for credential detection"
  - "_scope_to_mapping() for WinDev scope to Python pattern"
  - "format_global_state() returns markdown table with 5 columns"

# Metrics
duration: 3min
completed: 2026-01-24
---

# Phase 20 Plan 02: PromptBuilder Global State Integration Summary

**CONTEXT.md now includes Global State section with variables table and conversion patterns - covers GSTATE-04/05**

## Performance

| Metric | Value |
|--------|-------|
| Tasks | 2/2 |
| Duration | ~3 min |
| Files modified | 2 |
| Lines added | ~132 |

## What Was Built

### Task 1: Extend PromptBuilder with global state formatting

Added to `src/wxcode/services/prompt_builder.py` (416 lines total):

1. **Helper functions:**
   - `_is_sensitive_name(name)` - detects token/secret/password/key/pwd/auth/credential patterns
   - `_scope_to_mapping(scope)` - maps Scope enum to Python pattern recommendations

2. **Static methods on PromptBuilder:**
   - `format_global_state(global_state)` - creates markdown table with 5 columns:
     - Variable name, WLanguage type, default value (redacted if sensitive), scope, recommended mapping
   - `format_scope_patterns()` - returns detailed conversion pattern documentation

3. **Updated PROMPT_TEMPLATE:**
   - Added `## Global State ({global_var_count} variables)` section
   - Added `{global_state_table}` placeholder
   - Added `{scope_patterns}` placeholder

4. **Updated method signatures:**
   - `build_context()` - added `global_state: GlobalStateContext = None` parameter
   - `write_context_file()` - added `global_state: GlobalStateContext = None` parameter

### Task 2: Wire API to extract and pass global state

Updated `src/wxcode/api/output_projects.py`:

1. Added import for `extract_global_state_for_project`
2. In `initialize_output_project()` WebSocket handler:
   - Calls `await extract_global_state_for_project(output_project.kb_id)` after connections extraction
   - Sends WebSocket info message with variable count
   - Passes `global_state=global_state` to `PromptBuilder.write_context_file()`

## Requirements Covered

| Requirement | Implementation |
|-------------|----------------|
| GSTATE-04: Global variables table in CONTEXT.md | `format_global_state()` creates markdown table |
| GSTATE-05: Mapping pattern documented | `format_scope_patterns()` includes scope-to-pattern table |
| Sensitive data protection | `_is_sensitive_name()` redacts defaults for credential variables |

## Example Output

Generated CONTEXT.md will include:

```markdown
## Global State (5 variables)

| Variable | Type | Default | Scope | Recommended Mapping |
|----------|------|---------|-------|---------------------|
| `gCnn` | Connection | *none* | app | Environment variable / Settings class |
| `gsAccessToken` | string | *[REDACTED]* | app | Environment variable / Settings class |
| `gjParametros` | JSON | *none* | app | Environment variable / Settings class |
| `gnContador` | int | 0 | module | Module singleton / FastAPI Depends() |
| `gTabela` | array of stRecebiceisSi... | *none* | module | Module singleton / FastAPI Depends() |

### Scope Conversion Patterns

| Original Scope | Recommended Python Pattern |
|----------------|---------------------------|
| APP (Project Code) | Environment variables via `pydantic.BaseSettings` |
| MODULE (Set of Procedures) | FastAPI dependency injection or module-level singleton |
| REQUEST (Page-level) | Request context via `request.state` or `Depends()` |
```

## Key Links Verified

| From | To | Pattern |
|------|----|---------|
| output_projects.py | schema_extractor.py | `extract_global_state_for_project` import |
| output_projects.py | prompt_builder.py | `global_state=global_state` parameter |
| prompt_builder.py | PROMPT_TEMPLATE | `global_state_table`, `scope_patterns` placeholders |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

Phase 20 (Global State Extraction) is now complete. Ready for:
- Phase 21 (Init Context Assembly) - will combine schema, connections, and global state into unified initialization context
