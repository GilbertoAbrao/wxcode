# v4 Roadmap: Conceptual Restructure

**Milestone:** v4 Conceptual Restructure
**Created:** 2026-01-23
**Phases:** 7

## Overview

This milestone restructures wxcode's conceptual model and implements multi-stack support via LLM-driven generation. Instead of building deterministic code generators for each stack, we define stack characteristics and pass them to Claude Code via `/gsd:new-project`.

## Phase Summary

| Phase | Name | Requirements | Deliverables |
|-------|------|--------------|--------------|
| 14 | Data Models | R2, R5, R8 | Stack, OutputProject, Milestone models |
| 15 | Stack Configuration | R2 | 15 pre-configured stacks with metadata |
| 16 | Output Project UI | R3, R4 | Stack selection + Configuration selection |
| 17 | GSD Project Integration | R6, R7 | Prompt builder + auto-trigger /gsd:new-project |
| 18 | Milestone UI | R9 | Milestone creation from KB elements |
| 19 | GSD Milestone Integration | R10, R11 | Prompt builder + auto-trigger /gsd:new-milestone |
| 20 | UI Polish | R1, R12, R13 | Terminology, .planning tree, English UI |

## Phase 14: Data Models ✓

**Goal:** Create the core data models for multi-stack support.

**Requirements:** R2 (Stack Model), R5 (OutputProject), R8 (Milestone)

**Status:** COMPLETE (2026-01-23)

**Plans:** 2 plans

Plans:
- [x] 14-01-PLAN.md — Create Stack, OutputProject, Milestone models
- [x] 14-02-PLAN.md — Wire models (exports + Beanie registration)

**Deliverables:**
- [x] `Stack` model with full characteristics (13 fields)
- [x] `OutputProject` model with KB/Stack/Configuration references (8 fields)
- [x] `Milestone` model with OutputProject/Element references (6 fields)
- [x] MongoDB collections and indexes
- [x] Pydantic schemas for API

**Files:**
- `src/wxcode/models/stack.py` (created)
- `src/wxcode/models/output_project.py` (created)
- `src/wxcode/models/milestone.py` (created)

**Acceptance:**
- Models have all fields from REQUIREMENTS.md ✓
- Type hints complete ✓
- Beanie document configuration correct ✓

---

## Phase 15: Stack Configuration ✓

**Goal:** Pre-configure the 15 target stacks with full metadata.

**Requirements:** R2 (Stack Model)

**Status:** COMPLETE (2026-01-23)

**Plans:** 5 plans

Plans:
- [x] 15-01-PLAN.md — Create server-rendered stack YAML files (5 stacks)
- [x] 15-02-PLAN.md — Create SPA stack YAML files (5 stacks)
- [x] 15-03-PLAN.md — Create fullstack stack YAML files (5 stacks)
- [x] 15-04-PLAN.md — Create StackService (seed, query, group)
- [x] 15-05-PLAN.md — Integrate with startup + CLI command

**Deliverables:**
- [x] Stack seed data for all 15 combinations
- [x] Type mappings from HyperFile to each ORM
- [x] File structure templates per stack
- [x] Naming convention definitions
- [x] Import templates per stack
- [x] Example model templates per stack

**Stacks configured:**

**Server-rendered (5):**
1. FastAPI + Jinja2 ✓
2. FastAPI + HTMX ✓
3. Django + Templates ✓
4. Laravel + Blade ✓
5. Rails + ERB ✓

**SPA (5):**
6. FastAPI + React ✓
7. FastAPI + Vue ✓
8. NestJS + React (TypeORM) ✓
9. NestJS + Vue (TypeORM) ✓
10. Laravel + React ✓

**Fullstack (5):**
11. Next.js (App Router) ✓
12. Next.js (Pages) ✓
13. Nuxt 3 ✓
14. SvelteKit ✓
15. Remix ✓

**Files:**
- `src/wxcode/data/stacks/` (directory with 15 YAML configs)
- `src/wxcode/services/stack_service.py` (created)

**Acceptance:**
- All 15 stacks configured ✓
- Type mappings verified (28 HyperFile codes each) ✓
- Stack metadata sufficient for prompt engineering ✓

---

## Phase 16: Output Project UI ✓

**Goal:** Implement the output project creation flow with stack and configuration selection.

**Requirements:** R3 (Stack Selection), R4 (Configuration Selection)

**Status:** COMPLETE (2026-01-23)

**Plans:** 4 plans

Plans:
- [x] 16-01-PLAN.md — Backend API (Stacks + OutputProjects endpoints)
- [x] 16-02-PLAN.md — Frontend Foundation (TypeScript types + hooks)
- [x] 16-03-PLAN.md — Frontend UI (StackSelector, ConfigurationSelector, CreateProjectModal)
- [x] 16-04-PLAN.md — Integration + Verification (wire modal to KB page)

**Deliverables:**
- [x] API endpoints for OutputProject CRUD
- [x] API endpoint to list stacks (grouped)
- [x] API endpoint to list Configurations from KB
- [x] Stack selection modal (grouped by category)
- [x] Configuration selection dropdown
- [x] OutputProject creation flow
- [x] ProductTypeSelectorModal (two-step flow)

**UI Components:**
- `StackSelector` — Grouped radio buttons
- `ConfigurationSelector` — Dropdown with element counts
- `CreateProjectModal` — Combined flow
- `ProductTypeSelectorModal` — Product type selection (first step)

**Files:**
- `src/wxcode/api/output_projects.py` (created)
- `src/wxcode/api/stacks.py` (created)
- `frontend/src/components/output-project/` (directory)
- `frontend/src/components/product/ProductTypeSelectorModal.tsx` (created)
- `frontend/src/app/project/[id]/page.tsx` (modified)

**Acceptance:**
- User can select stack from grouped list ✓
- User can select Configuration from KB ✓
- OutputProject created with correct references ✓

---

## Phase 17: GSD Project Integration

**Goal:** Auto-trigger `/gsd:new-project` when output project is created.

**Requirements:** R6 (Prompt Engineering), R7 (Auto-trigger)

**Status:** PLANNED

**Plans:** 3 plans

Plans:
- [ ] 17-01-PLAN.md — Backend services (schema_extractor + prompt_builder)
- [ ] 17-02-PLAN.md — WebSocket endpoint for /initialize
- [ ] 17-03-PLAN.md — Frontend integration (hook + UI components)

**Deliverables:**
- [ ] Schema extractor (tables from Configuration)
- [ ] Prompt builder with stack + schema context
- [ ] Claude Code CLI invocation
- [ ] Streaming output to frontend
- [ ] Workspace initialization

**Prompt Structure:**
```markdown
# Project: {output_project.name}

## Target Stack
{stack characteristics as structured data}

## Schema
{tables with fields, types, constraints, relationships}

## Type Mappings
{HyperFile type → target ORM type}

## Project Structure
{expected file structure for this stack}

## Instructions
Generate a starter project with:
1. Models for all schema tables
2. Basic CRUD routes
3. Project configuration files
```

**Files:**
- `src/wxcode/services/prompt_builder.py` (new)
- `src/wxcode/services/schema_extractor.py` (new)
- `src/wxcode/api/output_projects.py` (extend with WebSocket)
- `frontend/src/components/output-project/InitializeButton.tsx` (new)
- `frontend/src/components/output-project/InitializeProgress.tsx` (new)

**Acceptance:**
- Prompt includes full stack characteristics
- Prompt includes Configuration schema
- Claude Code generates project in workspace
- Streaming output visible in UI

---

## Phase 18: Milestone UI

**Goal:** Implement milestone creation from KB elements.

**Requirements:** R9 (Milestone Creation)

**Deliverables:**
- [ ] API endpoints for Milestone CRUD
- [ ] API endpoint to list elements (filtered by Configuration)
- [ ] Element list with "Create Milestone" action
- [ ] Milestone creation modal with element context
- [ ] Dependency preview in modal

**UI Components:**
- `ElementList` — Filterable list of KB elements
- `CreateMilestoneModal` — Confirmation with dependencies
- `MilestoneList` — List of milestones in output project

**Files:**
- `src/wxcode/api/milestones.py` (new)
- `frontend/src/components/milestone/` (directory)
- `frontend/src/app/projects/[id]/milestones/` (page)

**Acceptance:**
- User can view elements in Configuration scope
- User can create milestone from element
- Milestone shows in output project view

---

## Phase 19: GSD Milestone Integration

**Goal:** Auto-trigger `/gsd:new-milestone` when milestone is created.

**Requirements:** R10 (Prompt Engineering), R11 (Auto-trigger)

**Deliverables:**
- [ ] Element context extractor (full element data)
- [ ] Control hierarchy extractor
- [ ] Dependency extractor (MongoDB + Neo4j)
- [ ] Prompt builder with element + stack context
- [ ] Claude Code CLI invocation
- [ ] Streaming output to frontend

**Prompt Structure:**
```markdown
# Milestone: Convert {element.source_name}

## Element
{raw_content, AST, procedures}

## Controls
{control hierarchy with events, bindings}

## Dependencies
{elements this element depends on}

## Schema Context
{tables used by this element}

## Target Stack
{stack characteristics from output project}

## Instructions
Convert this WinDev element to the target stack:
1. Create route/controller for this page
2. Create service layer for business logic
3. Create template/component for UI
4. Handle events and bindings
```

**Files:**
- `src/wxcode/services/element_context_builder.py` (new)
- `src/wxcode/services/prompt_builder.py` (enhance)
- `frontend/src/components/milestone/MilestoneProgress.tsx` (new)

**Acceptance:**
- Prompt includes full element context
- Prompt includes dependencies
- Claude Code converts element in workspace
- Streaming output visible in UI

---

## Phase 20: UI Polish

**Goal:** Apply terminology changes, add .planning tree view, convert UI to English.

**Requirements:** R1 (Terminology), R12 (.planning Tree), R13 (English)

**Deliverables:**
- [ ] Replace "Project" → "Knowledge Base" in UI
- [ ] Replace "Product" → "Project" in UI
- [ ] Replace "Conversion" → "Milestone" in UI
- [ ] .planning tree component in sidebar
- [ ] File viewer for .planning files
- [ ] All Portuguese text → English

**UI Components:**
- `PlanningTree` — File tree for .planning/
- `FileViewer` — Read-only file content display

**Files:**
- All frontend components (terminology sweep)
- `frontend/src/components/planning/` (directory)
- Translation/i18n updates

**Acceptance:**
- No "Project" referring to KB
- No "Product" referring to output project
- No "Conversion" referring to milestone
- .planning tree visible and functional
- No Portuguese text in UI

---

## Risk Mitigation

### LLM Generation Quality
**Risk:** Claude Code may generate inconsistent or incorrect code for some stacks.
**Mitigation:**
- Include comprehensive stack metadata (examples, conventions)
- Test generation for all 15 stacks during Phase 17
- Iterate on prompt structure based on results

### Prompt Size Limits
**Risk:** Large schemas or elements may exceed context limits.
**Mitigation:**
- Chunk large schemas intelligently
- Prioritize most relevant fields/dependencies
- Use summarization for very large elements

### Configuration Scope Accuracy
**Risk:** Configuration may not perfectly map to schema tables.
**Mitigation:**
- Use dependency analysis (Neo4j) to identify tables
- Allow manual table selection as fallback

## Success Metrics

| Metric | Target |
|--------|--------|
| Output project creation success rate | 95% |
| Claude Code generation success rate | 90% |
| Milestone conversion success rate | 85% |
| User can select stack and config | 100% |
| All 15 stacks selectable | 100% |

## Timeline Estimate

| Phase | Complexity | Estimate |
|-------|------------|----------|
| 14 | Low | 0.5 day |
| 15 | Medium | 1 day |
| 16 | Medium | 1 day |
| 17 | High | 1.5 days |
| 18 | Medium | 0.5 day |
| 19 | High | 1 day |
| 20 | Low | 0.5 day |
| **Total** | | **~6 days** |

---
*Created: 2026-01-23*
*Status: Ready for execution*
