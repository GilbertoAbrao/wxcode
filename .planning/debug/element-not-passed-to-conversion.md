---
status: resolved
trigger: "Element not passed to conversion - Nenhum elemento especificado para conversao"
created: 2026-01-22T10:00:00Z
updated: 2026-01-22T10:15:00Z
---

## Current Focus

hypothesis: CONFIRMED - element_names not passed in WebSocket start message
test: Traced data flow through all components
expecting: Found gap at line 206 in useConversionStream.ts
next_action: Document root cause

## Symptoms

expected: User selects element in wizard, creates product, "Iniciar Conversao" starts conversion for that element
actual: "Nenhum elemento especificado para conversao" error on product dashboard
errors: "Nenhum elemento especificado para conversao"
reproduction: Select element in wizard -> Create product -> Click "Iniciar Conversao"
started: Unknown - investigating

## Eliminated

- hypothesis: Product model missing element_names field
  evidence: Checked - Product model doesn't have this field, elements passed via query params
  timestamp: 2026-01-22T10:05:00Z

- hypothesis: API create endpoint doesn't accept element_names
  evidence: Confirmed - CreateProductRequest only has project_id and product_type
  timestamp: 2026-01-22T10:06:00Z

## Evidence

- timestamp: 2026-01-22T10:03:00Z
  checked: frontend/src/app/project/[id]/conversion/page.tsx (wizard)
  found: |
    Line 42-46: createProduct.mutateAsync({ project_id, product_type }) - NO element_names
    Line 50-52: Elements passed via URL query params: ?elements=PAGE_Login
  implication: Element names are NOT stored in Product, only passed via URL

- timestamp: 2026-01-22T10:05:00Z
  checked: src/wxcode/models/product.py
  found: |
    Product model has NO field for element_names or target_elements
    Only has: project_id, product_type, workspace_path, status, session_id, output_directory
  implication: Product doesn't store which elements to convert

- timestamp: 2026-01-22T10:06:00Z
  checked: src/wxcode/api/products.py - CreateProductRequest
  found: |
    Line 56-59: CreateProductRequest only has project_id and product_type
    Line 174-181: Product created without element info
  implication: Backend never receives element names during product creation

- timestamp: 2026-01-22T10:08:00Z
  checked: frontend/src/app/project/[id]/products/[productId]/page.tsx
  found: |
    Line 65-66: Elements read from URL searchParams
    Line 105-119: Auto-start if pending AND elementNames.length > 0
    Line 114: stream.start() called - BUT this doesn't pass element_names!
  implication: Frontend has the elements, but start() doesn't send them

- timestamp: 2026-01-22T10:10:00Z
  checked: frontend/src/hooks/useConversionStream.ts
  found: |
    Line 204-209: start() sends { action: "start" } - NO element_names!
  implication: WebSocket start message missing element_names

- timestamp: 2026-01-22T10:12:00Z
  checked: src/wxcode/api/products.py - WebSocket handler
  found: |
    Line 543-549: Expects element_names in the start message data
    if not element_names: send error "Nenhum elemento especificado"
  implication: Backend expects element_names but frontend never sends it

## Resolution

root_cause: |
  The useConversionStream hook's start() function (line 204-209) sends only
  { action: "start" } without including element_names. The product dashboard
  page has the element names from URL params (line 65-66) but the start()
  function doesn't accept parameters to pass them through.

  Data flow broken at:
  1. Wizard puts elements in URL: ?elements=PAGE_Login
  2. Product page reads them from URL: elementNamesParam.split(",")
  3. Product page calls stream.start() with NO params
  4. useConversionStream sends { action: "start" } - missing element_names
  5. Backend receives no element_names, returns error

fix: |
  Two changes needed:
  1. Modify useConversionStream.start() to accept element_names parameter
  2. Modify product dashboard to call stream.start(elementNames)

verification: pending
files_changed:
  - frontend/src/hooks/useConversionStream.ts
  - frontend/src/app/project/[id]/products/[productId]/page.tsx
