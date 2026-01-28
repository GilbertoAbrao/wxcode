# Milestone v4: Conceptual Restructure

**Status:** ✅ SHIPPED 2026-01-24
**Phases:** 14-18
**Total Plans:** 18

## Overview

Restructure concepts (KB/Output Projects/Milestones), add multi-stack support with LLM-driven generation, and improve GSD integration. Replaced deterministic code generators with LLM-driven approach using Claude Code and /gsd:new-project.

## Phases

### Phase 14: Data Models

**Goal:** Create Stack, OutputProject, and Milestone Beanie documents
**Depends on:** None
**Plans:** 2 plans

Plans:
- [x] 14-01: Create core data models (Stack, OutputProject, Milestone)
- [x] 14-02: Register models with Beanie and exports

**Details:**
- Stack model with 13 fields (orm_pattern, naming_conventions, file_structure, type_mappings)
- OutputProject model connecting KB to target Stack
- Milestone model tracking element conversion status
- PydanticObjectId for inter-document references

### Phase 15: Stack Configuration

**Goal:** Create 15 stack YAML configs and seeding service
**Depends on:** Phase 14
**Plans:** 5 plans

Plans:
- [x] 15-01: Create server-rendered stack configs (FastAPI, Django, Laravel, Rails)
- [x] 15-02: Create SPA stack configs (FastAPI + React/Vue/Svelte/Angular)
- [x] 15-03: Create fullstack stack configs (Next.js, Nuxt, SvelteKit, Laravel Inertia, Rails Hotwire)
- [x] 15-04: Create StackService for seeding and retrieval
- [x] 15-05: Create Stacks API endpoints

**Details:**
- 5 server-rendered + 5 SPA + 5 fullstack YAML configurations
- Complete type mappings for all 28 HyperFile types
- StackService with seed_stacks() and get_grouped()
- Stacks router with /grouped endpoint

### Phase 16: Output Project UI

**Goal:** Create Output Project CRUD UI with Stack/Configuration selection
**Depends on:** Phase 15
**Plans:** 4 plans

Plans:
- [x] 16-01: Create OutputProjects API endpoints
- [x] 16-02: Create frontend hooks and types
- [x] 16-03: Create StackSelector and ConfigurationSelector components
- [x] 16-04: Create CreateProjectModal and integrate into KB page

**Details:**
- Full CRUD API for Output Projects
- useStacks and useStacksGrouped hooks with 1-hour staleTime
- StackSelector with tabbed group navigation
- ConfigurationSelector with scope filtering
- CreateProjectModal with step-by-step flow

### Phase 17: GSD Project Integration

**Goal:** Connect Output Project initialization to Claude Code /gsd:new-project
**Depends on:** Phase 16
**Plans:** 3 plans

Plans:
- [x] 17-01: Create schema extractor and prompt builder services
- [x] 17-02: Create WebSocket endpoint for initialization
- [x] 17-03: Create frontend initialization UI

**Details:**
- SchemaExtractor extracts tables from selected Configuration
- PromptBuilder creates CONTEXT.md with stack characteristics + schema
- WebSocket streaming with real-time log messages
- GSDInvoker runs Claude CLI with /gsd:new-project
- InitializeButton and InitializeProgress components

### Phase 18: Milestone UI

**Goal:** Create Milestone CRUD UI for element-level conversion
**Depends on:** Phase 17
**Plans:** 4 plans

Plans:
- [x] 18-01: Create Milestones API endpoints
- [x] 18-02: Create Milestone frontend hooks and types
- [x] 18-03: Create CreateMilestoneModal component
- [x] 18-04: Integrate milestones into Output Project page

**Details:**
- Milestone API with CRUD and WebSocket initialization
- MilestonePromptBuilder collects element context (controls, procedures, dependencies)
- MilestonesTree component in sidebar
- FileTree component for real-time file visualization
- Complete flow: create milestone → select element → initialize with /gsd:new-project

---

## Milestone Summary

**Key Decisions:**

- LLM-driven generation (no deterministic generators) - Avoids maintaining 15+ generator implementations
- YAML files for stack configurations - Human-readable, supports comments
- WebSocket direct connection to backend - Next.js proxy doesn't support WS upgrade
- Schema extractor returns all tables as fallback - Handles missing element dependencies
- Use /gsd:new-project for both Output Project and Milestone initialization

**Issues Resolved:**

- MongoDB client initialization fixed in milestones API
- WebSocket URL construction for direct backend connection
- Schema extraction fallback when element dependencies not populated

**Technical Debt Incurred:**

None - all implementations follow established patterns.

**Deferred Items:**

- UI text in English (Portuguese acceptable for pt-BR market)
- .planning tree view in sidebar (FileTree provides similar value)

---

*For current project status, see .planning/STATE.md*
