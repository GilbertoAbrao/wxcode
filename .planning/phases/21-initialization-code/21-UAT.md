---
status: testing
phase: 21-initialization-code
source: [21-01-SUMMARY.md]
started: 2026-01-24T21:05:00Z
updated: 2026-01-24T21:05:00Z
---

## Current Test

number: 1
name: CONTEXT.md Has Initialization Code Section
expected: |
  After initializing an OutputProject from a KB with Project Code (windev_type=0), the generated CONTEXT.md includes "## Initialization Code" section with WLanguage code blocks showing startup code from the original project.
awaiting: user response

## Tests

### 1. CONTEXT.md Has Initialization Code Section
expected: After initializing an OutputProject from a KB with Project Code (windev_type=0), the generated CONTEXT.md includes "## Initialization Code" section with WLanguage code blocks showing startup code from the original project.
result: [pending]

### 2. Lifespan Pattern Documentation Shown
expected: When initialization blocks exist, CONTEXT.md includes FastAPI lifespan pattern documentation with @asynccontextmanager example and WLanguage-to-Python mapping table (HOpenConnection → create_async_engine, etc.).
result: [pending]

### 3. Long Code Blocks Truncated
expected: If initialization code exceeds 100 lines, it's truncated with "// ... (N more lines)" indicator to keep context manageable.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0

## Gaps

[none yet]
