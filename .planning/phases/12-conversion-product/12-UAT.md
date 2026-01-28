---
status: testing
phase: 12-conversion-product
source: [12-01-SUMMARY.md, 12-02-SUMMARY.md, 12-03-SUMMARY.md, 12-04-SUMMARY.md, 12-05-SUMMARY.md, 12-06-SUMMARY.md]
started: 2026-01-22T22:00:00Z
updated: 2026-01-23T00:00:00Z
---

## Current Test

number: 5
name: Product Dashboard Shows Streaming Output
expected: |
  Product dashboard displays terminal-like output area. When conversion starts, GSD output streams in real-time with auto-scroll.
  NOTE: The --output-format stream-json fix has been applied. Please retest.
awaiting: user response

## Tests

### 1. Open Conversion Wizard Page
expected: Navigate to /project/[id]/conversion. Page loads showing element selector with search box and list of elements from the project.
result: pass

### 2. Search Elements in Wizard
expected: Type in search box, element list filters in real-time to show only matching elements.
result: pass

### 3. Select Element for Conversion
expected: Click on an element in the list, it becomes highlighted/selected. "Iniciar Conversao" button becomes enabled.
result: pass

### 4. Start Conversion Creates Product
expected: Click "Iniciar Conversao", system creates Product record and redirects to /project/[id]/products/[productId] dashboard.
result: pass

### 5. Product Dashboard Shows Streaming Output
expected: Product dashboard displays terminal-like output area. When conversion starts, GSD output streams in real-time with auto-scroll.
result: [pending-retest]
note: "Previous issue with --output-format json fixed by commit 36abfb9. Needs retest."

### 6. Checkpoint Pauses Conversion
expected: When GSD completes a phase, conversion pauses and shows checkpoint UI with "Continuar" button. Status changes to PAUSED.
result: [pending]
note: "Previously skipped due to streaming issue. Now unblocked."

### 7. Resume Conversion After Checkpoint
expected: Click "Continuar" on checkpoint UI, conversion resumes from where it paused. Output continues streaming.
result: [pending]
note: "Previously skipped due to streaming issue. Now unblocked."

### 8. Product Appears in Factory Page
expected: After starting conversion, navigate to factory page. The created product appears in the list with status badge (IN_PROGRESS or PAUSED).
result: pass

## Summary

total: 8
passed: 5
issues: 0
pending: 3
skipped: 0

## Gaps

- truth: "Clicking Iniciar Conversao starts converting the element selected in wizard"
  status: closed
  reason: "Fixed by plan 12-06 - element_names now passed correctly"
  severity: blocker
  test: 5
  root_cause: "start() in useConversionStream doesn't accept/pass element_names. Product dashboard has elementNames from URL but calls stream.start() without passing them."
  fix_plan: "12-06-PLAN.md"

- truth: "GSD output streams in real-time with auto-scroll"
  status: closed
  reason: "Fixed by commit 36abfb9 - changed --output-format json to stream-json"
  severity: major
  test: 5
  root_cause: "GSDInvoker uses --output-format json which buffers all output until process completes. No streaming happens during execution."
  fix: "Changed to --output-format stream-json in gsd_invoker.py for real-time streaming"
