# Milestone v3: Product Factory

**Status:** ✅ SHIPPED 2026-01-23
**Phases:** 8-13
**Total Plans:** 18

## Overview

Transform wxcode from a converter into a product platform with isolated workspaces and multi-product UI. Each imported project creates an isolated workspace at `~/.wxcode/workspaces/` with its own KB. Users can create multiple products (conversion, API, MCP, agents) from the same KB.

## Phases

### Phase 8: Workspace Infrastructure
**Goal**: System creates and manages isolated workspaces for each imported project
**Depends on**: Nothing (first phase of v3)
**Requirements**: WORK-01, WORK-02, WORK-03, WORK-04
**Plans**: 1 plan

Plans:
- [x] 08-01-PLAN.md - WorkspaceManager service + WorkspaceMetadata model + tests

**Details:**
- Directory `~/.wxcode/workspaces/` created on first system interaction
- Workspace directories follow naming `{project_name}_{8char_id}/`
- Each workspace contains `.workspace.json` with project metadata
- Product subdirectories (`conversion/`, `api/`, `mcp/`, `agents/`) can be created

### Phase 9: Import Flow Update
**Goal**: Import wizard creates isolated workspace+KB for each project import
**Depends on**: Phase 8
**Requirements**: IMPRT-01, IMPRT-02, IMPRT-03, IMPRT-04
**Plans**: 2 plans

Plans:
- [x] 09-01-PLAN.md - Model updates + API integration (Project, ImportSession, create_session)
- [x] 09-02-PLAN.md - CLI + pipeline + cleanup (workspace flow completion)

**Details:**
- Import wizard creates workspace directory before processing files
- Project model links to workspace via `workspace_id` and `workspace_path`
- Importing same project twice creates two separate workspaces with distinct KBs
- Upload temp files are cleaned after import completes

### Phase 10: Product Model & API
**Goal**: Products are first-class entities with types, status, and CRUD API
**Depends on**: Phase 9
**Requirements**: PROD-01, PROD-02, PROD-03, PROD-04
**Plans**: 2 plans

Plans:
- [x] 10-01-PLAN.md - Product model + database registration
- [x] 10-02-PLAN.md - CRUD API endpoints + router registration

**Details:**
- Product model supports types: conversion, api, mcp, agents
- Each product has workspace_path, status, and session_id
- API endpoints support create, read, update, delete for products
- Products of types "api", "mcp", "agents" return status `unavailable`

### Phase 11: Product Selection UI
**Goal**: Users choose what to create from imported project via guided UI
**Depends on**: Phase 10
**Requirements**: UI-01, UI-02, UI-03, UI-04
**Plans**: 3 plans

Plans:
- [x] 11-01-PLAN.md - Product types + useProducts hook + import redirect
- [x] 11-02-PLAN.md - ProductCard + ProductGrid components
- [x] 11-03-PLAN.md - Factory page + sidebar navigation

**Details:**
- After import, user sees "O que vamos criar juntos?" page
- Product cards show name, description, and availability status
- Clicking enabled product navigates to product wizard
- Project page shows list of created products

### Phase 12: Conversion Product
**Goal**: Conversion product delivers element-by-element conversion with checkpoints
**Depends on**: Phase 11
**Requirements**: CONV-01, CONV-02, CONV-03, CONV-04, CONV-05, CONV-06
**Plans**: 6 plans (4 original + 2 gap closure)

Plans:
- [x] 12-01-PLAN.md - ConversionWizard service + resume endpoint (Wave 1)
- [x] 12-02-PLAN.md - Checkpoint detection + n8n fallback (Wave 1)
- [x] 12-03-PLAN.md - Conversion wizard page + element selector (Wave 2)
- [x] 12-04-PLAN.md - Product dashboard + streaming UI (Wave 2)
- [x] 12-05-PLAN.md - Gap closure: Wire product WebSocket + checkpoint detection (Wave 3)
- [x] 12-06-PLAN.md - Gap closure: Wire element_names from wizard to conversion (Wave 3)

**Details:**
- User can select specific element(s) to convert via wizard
- Each element conversion creates isolated `.planning/` directory in workspace
- GSDInvoker runs with `cwd` set to workspace_path
- Conversion works without N8N (local fallback)
- Conversion pauses at phase boundaries for user review
- User can resume paused conversion with `claude --continue`

### Phase 13: Progress & Output
**Goal**: Users have visibility into conversion progress and generated output
**Depends on**: Phase 12
**Requirements**: PROG-01, PROG-02, PROG-03, PROG-04
**Plans**: 4 plans

Plans:
- [x] 13-01-PLAN.md - Workspace files API + STATE.md parser + /progress endpoint (Wave 1)
- [x] 13-02-PLAN.md - ConversionHistory model + history API endpoints (Wave 1)
- [x] 13-03-PLAN.md - ProgressDashboard + OutputViewer components + integration (Wave 2)
- [x] 13-04-PLAN.md - ConversionHistory UI + factory page integration (Wave 2)

**Details:**
- Dashboard reads STATE.md from workspace and displays progress
- Output viewer shows generated code files
- "Continuar" button resumes paused conversion
- Project page shows history of all conversions

---

## Milestone Summary

**Key Decisions:**
- Workspace IDs: secrets.token_hex(4) for 8-char hex (consistent with gsd_context_collector)
- Name sanitization: lowercase + replace unsafe chars + limit 50 chars
- Product types: ['conversion', 'api', 'mcp', 'agents']
- AVAILABLE_PRODUCT_TYPES constant controls which products can be started (only conversion for now)
- Checkpoint detection via PHASE_COMPLETION_PATTERNS regex patterns
- Extended useConversionStream hook for checkpoint support (backward compatible)
- --output-format stream-json for real-time streaming (requires --verbose flag)

**Issues Resolved:**
- element_names not being passed from wizard to conversion (fixed in 12-06)
- GSD output buffering (--output-format json) replaced with stream-json

**Issues Deferred:**
- Full UAT testing of checkpoint flow (blocked by streaming issue, now fixed)

**Technical Debt:**
- --verbose flag requirement for stream-json discovered during UAT (fixed in v3 closure)

---

_For current project status, see .planning/ROADMAP.md_
